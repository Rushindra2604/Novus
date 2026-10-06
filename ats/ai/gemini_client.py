from __future__ import annotations

import os
from typing import Any

from google import genai


DEFAULT_MODEL = "gemini-3.5-flash-lite"


class GeminiClient:
    """Small wrapper around the Gemini API used by Novus ATS."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text from Gemini."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        config: dict[str, Any] = {}

        if system_instruction:
            config["system_instruction"] = system_instruction

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config or None,
        )

        text = getattr(response, "text", None)

        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response.")

        return text.strip()