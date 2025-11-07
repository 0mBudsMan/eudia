from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI


def build_llm(api_key: str | None, model: str) -> ChatGoogleGenerativeAI:
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing Gemini API key. Set the GOOGLE_API_KEY environment variable "
            "or pass --api-key."
        )

    return ChatGoogleGenerativeAI(
        model=model,
        api_key=key,
        temperature=0.2,
        top_p=0.8,
        convert_system_message_to_human=True,
    )
