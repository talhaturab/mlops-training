from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage, ToolMessage

from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


def _as_text(content) -> str:
    """Some providers return content as a list of parts; flatten to plain text."""
    if isinstance(content, str):
        return content
    return "".join(
        part.get("text", "") if isinstance(part, dict) else str(part) for part in content
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    graph = request.app.state.graph
    if graph is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "The Oracle is asleep: OPENROUTER_API_KEY is not set. Add it to .env and restart."
            ),
        )

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
