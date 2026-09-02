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


def _read_events(response) -> list[tuple[str, dict]]:
    import json

    events, current = [], {}
    for line in response.iter_lines():
        if line.startswith("event: "):
            current["event"] = line[len("event: ") :]
        elif line.startswith("data: "):
            current["data"] = json.loads(line[len("data: ") :])
        elif line == "" and current:
            events.append((current["event"], current["data"]))
            current = {}
    return events


def test_chat_stream_returns_503_without_llm_key(client):
    r = client.post("/chat/stream", json={"session_id": "st0", "message": "hi"})
    assert r.status_code == 503


def test_chat_stream_emits_tool_tokens_and_done(client, app):
    _install_fake_graph(app, [TOOL_CALL, AIMessage(content="A fine day awaits.")])
    with client.stream(
        "POST", "/chat/stream", json={"session_id": "st1", "message": "born 1990-08-15"}
    ) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = _read_events(r)

    names = [e for e, _ in events]
    assert names[0] == "tool" and events[0][1] == {"name": "get_horoscope"}
    assert "token" in names
    assert "".join(d["text"] for e, d in events if e == "token") == "A fine day awaits."
    assert events[-1] == ("done", {"tools_used": ["get_horoscope"]})
    assert client.get("/stats").json()["fortunes_told"] == 1


def test_chat_stream_reports_provider_error_as_event(client, app):
    class ExplodingModel(ScriptedChatModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            raise RuntimeError("upstream overloaded")

    app.state.graph = build_graph(
        ExplodingModel(responses=[AIMessage(content="unused")]), [get_horoscope], InMemorySaver()
    )
    with client.stream("POST", "/chat/stream", json={"session_id": "st2", "message": "hi"}) as r:
        events = _read_events(r)
    assert events[-1][0] == "error"
    assert "upstream overloaded" in events[-1][1]["detail"]
