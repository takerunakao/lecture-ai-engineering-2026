"""Day3 発展(a): 講座の指示・関数をそのまま使う Google ADK 版。"""

import os

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL


# 両版とも同じ Gemini Developer API・同じモデルを使用する。
# API キーはファイルに保存せず、Codespaces secret から読み取る。
# Client は ADK が実行時に作るため、API キーなしでも構成を検査できる。
client_options = {
    "enterprise": False,
    "http_options": types.HttpOptions(
        timeout=60_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
}
if os.getenv("GEMINI_API_KEY"):
    client_options["api_key"] = os.environ["GEMINI_API_KEY"]

root_agent = Agent(
    model=Gemini(model=MODEL, client_kwargs=client_options),
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary],
)
