"""A two-node ReAct loop: the model either calls a tool or answers.

START -> agent -> (tool calls?) -> tools -> agent -> ... -> END
"""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.persona import SYSTEM_PROMPT
from app.config import Settings


def create_llm(settings: Settings) -> ChatOpenAI:
    """OpenRouter speaks the OpenAI protocol, so the OpenAI client with another base_url works."""
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.llm_base_url,
        temperature=0.7,
        default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "The Oracle"},
    )


def build_graph(llm, tools: list, checkpointer=None):
    llm_with_tools = llm.bind_tools(tools)
    system = SystemMessage(content=SYSTEM_PROMPT)

    async def agent(state: MessagesState) -> dict:
        # The system prompt is prepended on every call and never stored in state.
        response = await llm_with_tools.ainvoke([system, *state["messages"]])
        return {"messages": [response]}

    def route(state: MessagesState) -> str:
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)
