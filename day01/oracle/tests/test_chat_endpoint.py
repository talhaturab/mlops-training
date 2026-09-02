from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.graph import build_graph
from tests.fakes import ScriptedChatModel

TOOL_CALL = AIMessage(
    content="",
    tool_calls=[
        {
            "name": "get_horoscope",
            "args": {"birthday": "1990-08-15"},
            "id": "c1",
            "type": "tool_call",
        }
    ],
)


@tool
def get_horoscope(birthday: str) -> str:
    """Fake horoscope tool."""
    return "Leo: a fine day"


def _install_fake_graph(app, responses):
    app.state.graph = build_graph(
        ScriptedChatModel(responses=responses), [get_horoscope], InMemorySaver()
    )


def test_chat_returns_503_without_llm_key(client):
    r = client.post("/chat", json={"session_id": "s1", "message": "hi"})
    assert r.status_code == 503
    assert "OPENROUTER_API_KEY" in r.json()["detail"]


def test_chat_returns_reply_and_tools_used(client, app):
    _install_fake_graph(app, [TOOL_CALL, AIMessage(content="A fine day awaits.")])
    r = client.post("/chat", json={"session_id": "s2", "message": "born 1990-08-15"})
    assert r.status_code == 200
    assert r.json() == {"reply": "A fine day awaits.", "tools_used": ["get_horoscope"]}
    assert client.get("/stats").json()["fortunes_told"] == 1


def test_chat_without_tools_does_not_count_a_fortune(client, app):
    _install_fake_graph(app, [AIMessage(content="Welcome, seeker. What is your name?")])
    r = client.post("/chat", json={"session_id": "s3", "message": "hello"})
    assert r.json()["tools_used"] == []
    assert client.get("/stats").json()["fortunes_told"] == 0


def test_chat_tools_used_only_counts_this_turn(client, app):
    _install_fake_graph(
        app, [TOOL_CALL, AIMessage(content="Done."), AIMessage(content="Anything else?")]
    )
    client.post("/chat", json={"session_id": "s4", "message": "first"})
    r = client.post("/chat", json={"session_id": "s4", "message": "second"})
    assert r.json()["tools_used"] == []


def test_chat_validates_input(client):
    assert client.post("/chat", json={"session_id": "", "message": "x"}).status_code == 422
