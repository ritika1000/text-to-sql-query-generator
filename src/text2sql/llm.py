"""Thin wrapper over any OpenAI-compatible chat API (Gemini, Groq, OpenRouter, ...)."""

from __future__ import annotations

import os


class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL")
        self._client = None

    def _get_client(self):
        missing = [
            name
            for name, value in [
                ("LLM_API_KEY", self.api_key),
                ("LLM_BASE_URL", self.base_url),
                ("LLM_MODEL", self.model),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing settings: {', '.join(missing)}. See .env.example.")
        if self._client is None:
            from openai import OpenAI  # imported lazily so tests don't need the SDK

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def complete(self, messages: list[dict]) -> str:
        response = self._get_client().chat.completions.create(
            model=self.model, messages=messages, temperature=0
        )
        return response.choices[0].message.content or ""
