"""ATS-01 resume analysis entry point.

This module adapts the existing Novus resume parser to the ATS pipeline.
It does not calculate an ATS score.
"""

from __future__ import annotations

from typing import Any

from .normalizer import normalize_resume_state


def build_resume_analysis(
    resume_text: str,
    *,
    fallback_title: str = "Untitled Resume",
    parser: Any,
) -> dict[str, Any]:
    """Extract -> parse -> normalize a resume for ATS analysis.

    `parser` is injected so the existing Novus parser remains the source of
    truth and ATS does not duplicate Resume Studio parsing logic.
    """
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Resume text is empty.")

    parsed_state = parser(resume_text, fallback_title=fallback_title)
    normalized = normalize_resume_state(parsed_state)

    normalized["source"] = {
        "fallback_title": fallback_title,
        "extracted_text": resume_text,
        "parser": "novus_resume_parser",
    }

    return normalized
