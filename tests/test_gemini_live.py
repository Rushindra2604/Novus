import os

import pytest

from ats.ai import GeminiClient


@pytest.mark.live
def test_gemini_live_connection():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        pytest.skip(
            "GEMINI_API_KEY is not configured."
        )

    client = GeminiClient()

    response = client.generate(
        "Reply with exactly: NOVUS GEMINI OK"
    )

    assert response
    assert "NOVUS GEMINI OK" in response.upper()