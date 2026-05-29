"""Day 22: Hello world Claude call with LangSmith tracing."""

import os

from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "verify-ai-copilot")

from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=256)


@traceable(name="hello_claude", run_type="llm")
def hello():
    response = llm.invoke("Say hello and confirm you are working. One sentence only.")
    return response.content


if __name__ == "__main__":
    print("Calling Claude via LangChain...")
    result = hello()
    print(f"Response: {result}")
    print("\nCheck LangSmith dashboard: https://smith.langchain.com/")
