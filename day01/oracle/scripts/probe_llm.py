"""Check that the configured OpenRouter model can call tools.

Run:  uv run python -m scripts.probe_llm   (or: make probe)
Prints PASS if the model returns a tool call for an obvious prompt, FAIL otherwise.
"""

import sys

from langchain_core.messages import HumanMessage

from app.agent.graph import create_llm
from app.agent.tools import get_horoscope
from app.config import get_settings


def main() -> int:
    settings = get_settings()
    if not settings.llm_configured:
        print("OPENROUTER_API_KEY is not set (put it in .env)")
        return 2
    llm = create_llm(settings).bind_tools([get_horoscope])
    print(f"model: {settings.llm_model}")
    response = llm.invoke([HumanMessage(content="I was born on 1990-08-15. What is my horoscope?")])
    print("content:", repr(response.content)[:200])
    print("tool_calls:", response.tool_calls)
    if response.tool_calls and response.tool_calls[0]["name"] == "get_horoscope":
        print("PASS: model supports tool calling")
        return 0
    print("FAIL: no tool call returned. Try another LLM_MODEL in .env.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
