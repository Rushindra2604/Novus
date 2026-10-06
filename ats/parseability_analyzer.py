"""
Novus ATS - Resume Parseability Analyzer

Evaluates whether a resume is reasonably structured and machine-readable
for ATS processing.

This module does NOT:
- calculate keyword matching
- analyze job-description relevance
- use AI
- rewrite resume content
- judge visual design aesthetics

It focuses only on resume structure and parseability.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return value.strip()


def _safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _check(
    *,
    score: float,
    status: str,
    message: str,
) -> dict[str, Any]:
    return {
        "score": round(max(0.0, min(100.0, score)), 2),
        "status": status,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _analyze_text_extractability(
    resume_text: str,
) -> dict[str, Any]:
    text = _safe_text(resume_text)

    if not text:
        return _check(
            score=0,
            status="fail",
            message="No resume text could be extracted.",
        )

    character_count = len(text)
    word_count = len(re.findall(r"\b\w+\b", text))

    if word_count < 50:
        return _check(
            score=40,
            status="warning",
            message="Very little resume text was extracted.",
        )

    if word_count < 100:
        return _check(
            score=70,
            status="warning",
            message="Resume text was extracted, but the document appears short.",
        )

    return _check(
        score=100,
        status="pass",
        message="Resume text was successfully extracted.",
    )


# ---------------------------------------------------------------------------
# Section structure
# ---------------------------------------------------------------------------

_SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "objective",
        "career objective",
    },
    "education": {
        "education",
        "academic background",
        "academic qualifications",
    },
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "technical expertise",
        "technologies",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "internship",
        "internships",
    },
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
        "project experience",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses & certifications",
    },
}


def _normalize_heading(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[:\-–—]+$", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _detect_sections(resume_text: str) -> dict[str, bool]:
    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    detected = {
        section: False
        for section in _SECTION_ALIASES
    }

    for line in lines:
        heading = _normalize_heading(line)

        for section, aliases in _SECTION_ALIASES.items():
            if heading in aliases:
                detected[section] = True

    return detected


def _analyze_section_structure(
    resume_text: str,
    resume_analysis: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:

    detected = _detect_sections(resume_text)

    parsed_sections = {
        "summary": bool(
            _safe_text(resume_analysis.get("summary"))
        ),
        "education": bool(
            _safe_list(resume_analysis.get("education"))
        ),
        "skills": bool(
            resume_analysis.get("skills")
        ),
        "experience": bool(
            _safe_list(resume_analysis.get("experience"))
        ),
        "projects": bool(
            _safe_list(resume_analysis.get("projects"))
        ),
        "certifications": bool(
            _safe_list(resume_analysis.get("certifications"))
        ),
    }

    # A section can be represented either by a detectable heading or
    # successfully parsed structured content.
    effective = {
        section: detected[section] or parsed_sections[section]
        for section in detected
    }

    important_sections = [
        "education",
        "skills",
    ]

    optional_sections = [
        "summary",
        "experience",
        "projects",
        "certifications",
    ]

    important_score = sum(
        1 for section in important_sections
        if effective[section]
    )

    optional_score = sum(
        1 for section in optional_sections
        if effective[section]
    )

    score = (
        (important_score / len(important_sections)) * 60
        +
        (optional_score / len(optional_sections)) * 40
    )

    if score >= 85:
        status = "pass"
        message = "Resume sections are clearly structured."
    elif score >= 60:
        status = "warning"
        message = "Resume has a usable structure but some sections are unclear or missing."
    else:
        status = "fail"
        message = "Resume section structure is difficult to identify."

    return (
        _check(
            score=score,
            status=status,
            message=message,
        ),
        effective,
    )


# ---------------------------------------------------------------------------
# Contact information
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.I,
)

_PHONE_RE = re.compile(
    r"(?<!\d)"
    r"(?:\+?\d{1,3}[\s.-]?)?"
    r"(?:\(?\d{3,4}\)?[\s.-]?)?"
    r"\d{3,4}[\s.-]?\d{4}"
    r"(?!\d)"
)


def _analyze_contact_information(
    resume_text: str,
    resume_analysis: dict[str, Any],
) -> dict[str, Any]:

    personal = resume_analysis.get("personal")

    if not isinstance(personal, dict):
        personal = {}

    email = _safe_text(personal.get("email"))
    phone = _safe_text(personal.get("phone"))
    full_name = _safe_text(personal.get("full_name"))

    if not email:
        email_match = _EMAIL_RE.search(resume_text)
        email = email_match.group(0) if email_match else ""

    if not phone:
        phone_match = _PHONE_RE.search(resume_text)
        phone = phone_match.group(0) if phone_match else ""

    if not full_name:
        lines = [
            line.strip()
            for line in resume_text.splitlines()
            if line.strip()
        ]

        if lines:
            first_line = lines[0]

            if (
                len(first_line.split()) <= 5
                and not _EMAIL_RE.search(first_line)
            ):
                full_name = first_line

    found = sum(
        bool(value)
        for value in [full_name, email, phone]
    )

    score = {
        0: 20,
        1: 50,
        2: 80,
        3: 100,
    }[found]

    if found == 3:
        status = "pass"
        message = "Name, email, and phone information are detectable."
    elif found >= 2:
        status = "warning"
        message = "Most core contact information is detectable."
    else:
        status = "fail"
        message = "Important contact information is difficult to detect."

    return _check(
        score=score,
        status=status,
        message=message,
    )


# ---------------------------------------------------------------------------
# Content structure
# ---------------------------------------------------------------------------

def _count_bullets(resume_text: str) -> int:
    return len(
        re.findall(
            r"(?m)^\s*[•▪◦‣⁃\-]\s+",
            resume_text,
        )
    )


def _analyze_content_structure(
    resume_text: str,
    resume_analysis: dict[str, Any],
) -> dict[str, Any]:

    bullet_count = _count_bullets(resume_text)

    projects = _safe_list(
        resume_analysis.get("projects")
    )

    experience = _safe_list(
        resume_analysis.get("experience")
    )

    descriptions = 0

    for item in projects + experience:
        if not isinstance(item, dict):
            continue

        for key in (
            "description",
            "details",
            "bullets",
            "responsibilities",
            "achievements",
        ):
            value = item.get(key)

            if isinstance(value, str) and value.strip():
                descriptions += 1
                break

            if isinstance(value, list) and value:
                descriptions += 1
                break

    score = 40.0

    if bullet_count >= 2:
        score += 30

    if descriptions >= 1:
        score += 20

    if bullet_count >= 5:
        score += 10

    score = min(score, 100)

    if score >= 80:
        status = "pass"
        message = "Resume contains reasonably structured content."
    elif score >= 60:
        status = "warning"
        message = "Resume content is usable but could be structured more consistently."
    else:
        status = "fail"
        message = "Resume content structure may be difficult for ATS extraction."

    return _check(
        score=score,
        status=status,
        message=message,
    )


# ---------------------------------------------------------------------------
# Date structure
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(
    r"\b(?:"
    r"19|20"
    r")\d{2}\b"
)


def _analyze_date_structure(
    resume_text: str,
) -> dict[str, Any]:

    years = _DATE_RE.findall(resume_text)

    year_count = len(years)

    if year_count == 0:
        return _check(
            score=60,
            status="warning",
            message="No recognizable year-based dates were detected.",
        )

    if year_count >= 2:
        return _check(
            score=100,
            status="pass",
            message="Resume contains recognizable date information.",
        )

    return _check(
        score=80,
        status="warning",
        message="Some date information is detectable, but the resume may contain limited timeline information.",
    )


# ---------------------------------------------------------------------------
# Length
# ---------------------------------------------------------------------------

def _analyze_length(
    resume_text: str,
) -> dict[str, Any]:

    words = re.findall(
        r"\b\w+\b",
        resume_text,
    )

    word_count = len(words)

    if 150 <= word_count <= 1200:
        return _check(
            score=100,
            status="pass",
            message="Resume length is within a reasonable range.",
        )

    if 80 <= word_count < 150:
        return _check(
            score=75,
            status="warning",
            message="Resume appears shorter than expected.",
        )

    if 1200 < word_count <= 1600:
        return _check(
            score=80,
            status="warning",
            message="Resume is somewhat long and may contain unnecessary content.",
        )

    if word_count > 1600:
        return _check(
            score=55,
            status="warning",
            message="Resume is unusually long and may contain excessive content.",
        )

    return _check(
        score=35,
        status="fail",
        message="Resume contains very little textual content.",
    )


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

def analyze_parseability(
    resume_text: str,
    resume_analysis: dict[str, Any],
) -> dict[str, Any]:

    if not isinstance(resume_text, str):
        raise ValueError("Resume text must be a string.")

    if not isinstance(resume_analysis, dict):
        raise ValueError("Resume analysis must be a dictionary.")

    text_check = _analyze_text_extractability(
        resume_text
    )

    section_check, detected_sections = _analyze_section_structure(
        resume_text,
        resume_analysis,
    )

    contact_check = _analyze_contact_information(
        resume_text,
        resume_analysis,
    )

    content_check = _analyze_content_structure(
        resume_text,
        resume_analysis,
    )

    date_check = _analyze_date_structure(
        resume_text
    )

    length_check = _analyze_length(
        resume_text
    )

    checks = {
        "text_extractability": text_check,
        "section_structure": section_check,
        "contact_information": contact_check,
        "content_structure": content_check,
        "date_structure": date_check,
        "length": length_check,
    }

    # Weighted internal parseability score.
    #
    # Text extraction is most important because an ATS cannot evaluate
    # information it cannot extract.
    weights = {
        "text_extractability": 25,
        "section_structure": 25,
        "contact_information": 15,
        "content_structure": 15,
        "date_structure": 10,
        "length": 10,
    }

    score = sum(
        checks[name]["score"] * weight / 100
        for name, weight in weights.items()
    )

    score = round(score, 2)

    strengths = []
    issues = []

    for name, result in checks.items():
        if result["status"] == "pass":
            strengths.append(result["message"])
        elif result["status"] in {"warning", "fail"}:
            issues.append(result["message"])

    if score >= 85:
        overall_status = "excellent"
    elif score >= 70:
        overall_status = "good"
    elif score >= 55:
        overall_status = "moderate"
    else:
        overall_status = "needs_improvement"

    return {
        "schema_version": "1.0",
        "score": score,
        "status": overall_status,
        "checks": checks,
        "detected_sections": detected_sections,
        "strengths": strengths,
        "issues": issues,
        "weights": weights,
        "stats": {
            "character_count": len(resume_text),
            "word_count": len(
                re.findall(r"\b\w+\b", resume_text)
            ),
            "bullet_count": _count_bullets(resume_text),
            "detected_section_count": sum(
                detected_sections.values()
            ),
        },
    }


__all__ = [
    "analyze_parseability",
]