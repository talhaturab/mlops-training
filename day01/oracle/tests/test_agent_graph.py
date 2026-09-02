from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.graph import build_graph
from app.agent.persona import SYSTEM_PROMPT
from tests.fakes import ScriptedChatModel


@tool
def get_horoscope(birthday: str) -> str:
    """Fake horoscope tool."""
    return f"Leo: a fine day for {birthday}"


def _scripted_llm():
    return ScriptedChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_horoscope",
                        "args": {"birthday": "1990-08-15"},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="The stars have spoken: a fine day."),
        ]
    )


async def test_graph_runs_tool_then_answers():
    llm = _scripted_llm()
    graph = build_graph(llm, [get_horoscope], InMemorySaver())
    config = {"configurable": {"thread_id": "t1"}}
    result = await graph.ainvoke({"messages": [HumanMessage(content="Born 1990-08-15")]}, config)
    msgs = result["messages"]
    assert isinstance(msgs[-1], AIMessage)
    assert msgs[-1].content == "The stars have spoken: a fine day."
    tool_msgs = [m for m in msgs if isinstance(m, ToolMessage)]
    assert [m.name for m in tool_msgs] == ["get_horoscope"]
    assert "Leo" in tool_msgs[0].content
    # The persona must be the first message of every model call.
    assert len(llm.calls) == 2
    for call in llm.calls:
        assert isinstance(call[0], SystemMessage)
        assert call[0].content == SYSTEM_PROMPT


async def test_graph_keeps_history_per_thread():
    graph = build_graph(_scripted_llm(), [get_horoscope], InMemorySaver())
    config = {"configurable": {"thread_id": "t2"}}
    await graph.ainvoke({"messages": [HumanMessage(content="hello")]}, config)
    await graph.ainvoke({"messages": [HumanMessage(content="again")]}, config)
    history = (await graph.aget_state(config)).values["messages"]
    assert sum(isinstance(m, HumanMessage) for m in history) == 2
    assert not any(isinstance(m, SystemMessage) for m in history)


def test_system_prompt_mentions_disclaimers():
    assert "invented" in SYSTEM_PROMPT.lower()
    assert "survey" in SYSTEM_PROMPT.lower()


async def test_graph_retries_transient_model_failures():
    class FlakyModel(ScriptedChatModel):
        failures_left: int = 2

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            if self.failures_left > 0:
                self.failures_left -= 1
                raise RuntimeError("Service temporarily overloaded")
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    llm = FlakyModel(responses=[AIMessage(content="Third time lucky.")])
    graph = build_graph(llm, [get_horoscope], InMemorySaver(), max_attempts=3)
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="hi")]}, {"configurable": {"thread_id": "r1"}}
    )
    assert result["messages"][-1].content == "Third time lucky."


def test_reasoning_body_levels():
    from app.agent.graph import reasoning_body

    assert reasoning_body("off") == {"reasoning": {"enabled": False}}
    assert reasoning_body("low") == {"reasoning": {"effort": "low"}}
