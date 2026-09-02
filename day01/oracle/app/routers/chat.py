import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.schemas import ChatRequest, ChatResponse

router = APIRouter()

ASLEEP_DETAIL = "The Oracle is asleep: OPENROUTER_API_KEY is not set. Add it to .env and restart."


def _as_text(content) -> str:
    """Some providers return content as a list of parts; flatten to plain text."""
    if isinstance(content, str):
        return content
    return "".join(
        part.get("text", "") if isinstance(part, dict) else str(part) for part in content
    )


def _require_graph(request: Request):
    graph = request.app.state.graph
    if graph is None:
        raise HTTPException(status_code=503, detail=ASLEEP_DETAIL)
    return graph


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """One request, one complete reply. Simple to call from curl or a test."""
    graph = _require_graph(request)
    config = {"configurable": {"thread_id": body.session_id}}
    before = len((await graph.aget_state(config)).values.get("messages", []))
    try:
        result = await graph.ainvoke({"messages": [HumanMessage(content=body.message)]}, config)
    except Exception as exc:  # noqa: BLE001 - deliberately broad on Day 1: any failure
        # inside the graph (provider, tool code, recursion limit) is reported to the caller.
        raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}") from exc

    new_messages = result["messages"][before:]
    tools_used = [m.name for m in new_messages if isinstance(m, ToolMessage)]
    if tools_used:
        request.app.state.store.record_fortune()
    return ChatResponse(reply=_as_text(result["messages"][-1].content), tools_used=tools_used)


def _sse(event: str, data: dict) -> str:
    """One Server-Sent Event: an event name and a JSON payload, terminated by a blank line."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    """Same conversation as /chat, but tokens are pushed as they arrive.

    Events: `token` {text}, `tool` {name} when a tool finishes, `error` {detail}, and
    finally `done` {tools_used}. The browser reads these with a streaming fetch.
    """
    graph = _require_graph(request)
    config = {"configurable": {"thread_id": body.session_id}}
    store = request.app.state.store

    async def events() -> AsyncIterator[str]:
        tools_used: list[str] = []
        try:
            stream = graph.astream(
                {"messages": [HumanMessage(content=body.message)]},
                config,
                stream_mode="messages",
            )
            async for message, metadata in stream:
                if isinstance(message, ToolMessage):
                    tools_used.append(message.name)
                    yield _sse("tool", {"name": message.name})
                elif isinstance(message, AIMessage) and metadata.get("langgraph_node") == "agent":
                    text = _as_text(message.content)
                    if text:
                        yield _sse("token", {"text": text})
        except Exception as exc:  # noqa: BLE001 - same reasoning as /chat
            yield _sse("error", {"detail": f"LLM provider error: {exc}"})
            return
        if tools_used:
            store.record_fortune()
        yield _sse("done", {"tools_used": tools_used})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
