"""
Novus ATS - Job Description Parser

Converts raw job descriptions into a deterministic, normalized structure
that can be consumed by the ATS matching and scoring engines.

This module does not:
- calculate ATS scores
- compare a resume against a job description
- use AI
- rewrite job descriptions
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Common technical skills / keywords
# ---------------------------------------------------------------------------

KNOWN_TECHNICAL_TERMS = {
    # Programming languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "go",
    "golang",
    "rust",
    "kotlin",
    "swift",
    "php",
    "ruby",
    "scala",

    # Web
    "html",
    "css",
    "react",
    "react.js",
    "angular",
    "vue",
    "next.js",
    "node.js",
    "node",
    "express",
    "django",
    "flask",
    "fastapi",

    # Databases
    "sql",
    "mysql",
    "postgresql",
    "postgres",
    "mongodb",
    "sqlite",
    "redis",
    "oracle",

    # Cloud / DevOps
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "docker",
    "kubernetes",
    "terraform",
    "jenkins",
    "github actions",
    "ci/cd",
    "linux",

    # Data / AI
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "ai",
    "data science",
    "data analysis",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "nlp",

    # Software engineering
    "rest api",
    "restful api",
    "api",
    "microservices",
    "git",
    "github",
    "gitlab",
    "unit testing",
    "testing",
    "debugging",
    "object-oriented programming",
    "oop",
    "data structures",
    "algorithms",

    # Tools
    "jira",
    "confluence",
    "postman",
    "figma",
}


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

SECTION_ALIASES = {
    "responsibilities": {
        "responsibilities",
        "responsibility",
        "what you'll do",
        "what you will do",
        "key responsibilities",
        "roles and responsibilities",
        "duties",
    },
    "requirements": {
        "requirements",
        "required qualifications",
        "required skills",
        "qualifications",
        "basic qualifications",
        "minimum qualifications",
        "must have",
        "what we're looking for",
        "what we are looking for",
    },
    "preferred": {
        "preferred qualifications",
        "preferred skills",
        "preferred",
        "nice to have",
        "nice-to-have",
        "good to have",
        "bonus qualifications",
        "additional qualifications",
    },
    "education": {
        "education",
        "educational qualifications",
        "academic qualifications",
    },
    "about": {
        "about",
        "about the role",
        "about the company",
        "job description",
        "overview",
        "summary",
    },
}


def _clean_line(line: str) -> str:
    """Normalize whitespace without changing the actual meaning."""
    return re.sub(r"\s+", " ", line).strip()


def _normalize_heading(line: str) -> str:
    """Convert a heading into a comparable normalized form."""
    value = line.strip().lower()
    value = re.sub(r"[:\-]+$", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _detect_section(line: str) -> str | None:
    """Return the canonical section name for a recognized heading."""
    normalized = _normalize_heading(line)

    for section_name, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section_name

    return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _deduplicate(values: list[str]) -> list[str]:
    """
    Remove duplicates while preserving their original order.
    """
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        cleaned = _clean_line(value)

        if not cleaned:
            continue

        key = cleaned.lower()

        if key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def _split_bullets(text: str) -> list[str]:
    """
    Convert common bullet/list formatting into individual items.
    """
    items: list[str] = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        line = re.sub(
            r"^(?:[-*•▪◦‣]|\d+[.)])\s*",
            "",
            line,
        )

        if line:
            items.append(_clean_line(line))

    return _deduplicate(items)


def _extract_sentences(text: str) -> list[str]:
    """
    Split prose into simple sentences.

    This intentionally stays deterministic and lightweight.
    """
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    return _deduplicate(sentences)


# ---------------------------------------------------------------------------
# Required / preferred classification
# ---------------------------------------------------------------------------

REQUIRED_MARKERS = (
    "required",
    "must have",
    "must-have",
    "mandatory",
    "essential",
    "minimum",
    "need to have",
    "should have",
)

PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "good to have",
    "bonus",
    "plus",
    "ideally",
    "desired",
)


def _contains_marker(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()

    return any(marker in lowered for marker in markers)


def _classify_requirement_lines(
    lines: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """
    Classify requirement lines into required, preferred and ambiguous.

    Ambiguous requirements are preserved separately rather than incorrectly
    assuming that every requirement is mandatory.
    """
    required: list[str] = []
    preferred: list[str] = []
    ambiguous: list[str] = []

    for line in lines:
        if _contains_marker(line, REQUIRED_MARKERS):
            required.append(line)
        elif _contains_marker(line, PREFERRED_MARKERS):
            preferred.append(line)
        else:
            ambiguous.append(line)

    return (
        _deduplicate(required),
        _deduplicate(preferred),
        _deduplicate(ambiguous),
    )


def _extract_skills_from_lines(lines: list[str]) -> list[str]:
    """
    Extract known technical skills from requirement lines.

    This is used when a JD groups skills under an explicit
    Required Skills / Preferred Skills section without repeating
    words such as "required" on every line.
    """
    if not isinstance(lines, list):
        return []

    text = "\n".join(
        line for line in lines
        if isinstance(line, str) and line.strip()
    )

    if not text:
        return []

    return _extract_technical_keywords(text)


# ---------------------------------------------------------------------------
# Technical keyword extraction
# ---------------------------------------------------------------------------

def _term_pattern(term: str) -> str:
    """
    Build a regex pattern for a technical term.

    Special handling is included for terms such as C++, C#, Node.js etc.
    """
    escaped = re.escape(term)

    # Terms containing punctuation need slightly relaxed boundaries.
    if re.search(r"[^a-zA-Z0-9\s]", term):
        return rf"(?<!\w){escaped}(?!\w)"

    return rf"(?<!\w){escaped}(?!\w)"


def _extract_technical_keywords(text: str) -> list[str]:
    """
    Extract known technical terms from the job description.

    Matching is case-insensitive and supports multi-word technologies.
    """
    found: list[str] = []

    lowered = text.lower()

    for term in KNOWN_TECHNICAL_TERMS:
        pattern = _term_pattern(term)

        if re.search(pattern, lowered, flags=re.IGNORECASE):
            found.append(term)

    # Prefer deterministic alphabetical ordering.
    return sorted(
        _deduplicate(found),
        key=lambda value: value.lower(),
    )


# ---------------------------------------------------------------------------
# Experience extraction
# ---------------------------------------------------------------------------

EXPERIENCE_PATTERNS = (
    r"\b\d+\+?\s*(?:-|to)?\s*\d*\s*years?\s+(?:of\s+)?experience\b",
    r"\bexperience\s+of\s+\d+\+?\s*(?:-|to)?\s*\d*\s*years?\b",
    r"\bminimum\s+\d+\+?\s*years?\b",
)


def _extract_experience_requirements(text: str) -> list[str]:
    """
    Extract sentences/lines containing explicit experience requirements.
    """
    candidates: list[str] = []

    for sentence in _extract_sentences(text):
        if any(
            re.search(pattern, sentence, flags=re.IGNORECASE)
            for pattern in EXPERIENCE_PATTERNS
        ):
            candidates.append(sentence)

    return _deduplicate(candidates)


# ---------------------------------------------------------------------------
# Education extraction
# ---------------------------------------------------------------------------

EDUCATION_TERMS = (
    "bachelor",
    "bachelor's",
    "master",
    "master's",
    "degree",
    "b.tech",
    "btech",
    "m.tech",
    "mtech",
    "b.e.",
    "b.e",
    "m.e.",
    "m.e",
    "mba",
    "phd",
    "ph.d",
    "computer science",
    "information technology",
)


def _extract_education_requirements(text: str) -> list[str]:
    """
    Extract lines/sentences that appear to describe education requirements.
    """
    candidates: list[str] = []

    for sentence in _extract_sentences(text):
        lowered = sentence.lower()

        if any(term in lowered for term in EDUCATION_TERMS):
            candidates.append(sentence)

    return _deduplicate(candidates)


# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------

def _parse_sections(text: str) -> dict[str, str]:
    """
    Parse recognized headings and collect the text below each heading.

    Unrecognized text is stored under 'general'.
    """
    sections: dict[str, list[str]] = {
        "general": [],
        "about": [],
        "responsibilities": [],
        "requirements": [],
        "preferred": [],
        "education": [],
    }

    current_section = "general"

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)

        if not line:
            continue

        detected = _detect_section(line)

        if detected:
            current_section = detected
            continue

        sections[current_section].append(line)

    return {
        name: "\n".join(_deduplicate(lines))
        for name, lines in sections.items()
    }


# ---------------------------------------------------------------------------
# Job title extraction
# ---------------------------------------------------------------------------

TITLE_PATTERNS = (
    r"^\s*(?:job\s+title|position|role)\s*:\s*(.+)$",
    r"^\s*(?:job\s+title|position|role)\s+(.+)$",
)


def _extract_title(text: str) -> str:
    """
    Try to extract a job title from an explicit Job Title / Position / Role
    line. Return an empty string if none is found.
    """
    for raw_line in text.splitlines():
        line = _clean_line(raw_line)

        if not line:
            continue

        for pattern in TITLE_PATTERNS:
            match = re.match(pattern, line, flags=re.IGNORECASE)

            if match:
                return _clean_line(match.group(1))

    return ""


# ---------------------------------------------------------------------------
# Public parser
# ---------------------------------------------------------------------------

def parse_job_description(text: str) -> dict[str, Any]:
    """
    Parse a raw job description into the Novus ATS JD structure.

    Args:
        text: Raw job description text.

    Returns:
        A normalized job description dictionary.

    Raises:
        ValueError: If the input is empty or not a string.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Job description is empty.")

    raw_text = text.strip()

    sections = _parse_sections(raw_text)

    # ------------------------------------------------------------------
    # Required / preferred skills
    # ------------------------------------------------------------------

    # Collect requirement lines from the explicit requirements section.
    requirement_lines = []

    if sections["requirements"]:
        requirement_lines.extend(
            _split_bullets(sections["requirements"])
        )

    required, preferred, ambiguous = _classify_requirement_lines(
        requirement_lines
    )

    # --------------------------------------------------------------
    # Skills inside an explicit "Requirements / Required Skills"
    # section are treated as required when they are known technical
    # skills and were not explicitly marked preferred.
    # --------------------------------------------------------------
    required_section_skills = _extract_skills_from_lines(
        requirement_lines
    )

    # --------------------------------------------------------------
    # Explicit preferred section is always treated as preferred.
    # --------------------------------------------------------------
    preferred_lines = _split_bullets(
        sections["preferred"]
    )

    # If the preferred section contains plain lines instead of bullets,
    # preserve those lines as individual requirements.
    if not preferred_lines and sections["preferred"]:
        preferred_lines = [
            line.strip()
            for line in sections["preferred"].splitlines()
            if line.strip()
        ]

    preferred.extend(preferred_lines)

    preferred_section_skills = _extract_skills_from_lines(
        preferred_lines
    )

    preferred.extend(preferred_section_skills)

    # --------------------------------------------------------------
    # Add technical skills from requirement lines to required skills.
    # Remove anything that also appears in preferred skills.
    # --------------------------------------------------------------
    required.extend(required_section_skills)

    preferred = _deduplicate(preferred)

    preferred_normalized = {
        value.lower()
        for value in preferred
    }

    required = _deduplicate(
        [
            value
            for value in required
            if value.lower() not in preferred_normalized
        ]
    )

    preferred = _deduplicate(preferred)

    # Education requirements.
    education_requirements = _extract_education_requirements(raw_text)

    # Experience requirements.
    experience_requirements = _extract_experience_requirements(raw_text)

    # Responsibilities.
    responsibilities = _split_bullets(
        sections["responsibilities"]
    )

    # Technical keywords from the entire JD.
    technical_keywords = _extract_technical_keywords(raw_text)

    # Other requirements are requirements that couldn't safely be classified
    # as required/preferred.
    other_requirements = _deduplicate(
        ambiguous + education_requirements
    )

    # The canonical searchable text is deliberately based on the complete
    # source rather than only extracted keywords. ATS-03 can then perform
    # more sophisticated matching without losing context.
    searchable_text = _clean_line(
        " ".join(
            [
                sections["general"],
                sections["about"],
                sections["responsibilities"],
                sections["requirements"],
                sections["preferred"],
                sections["education"],
            ]
        )
    )

    return {
        "schema_version": "1.0",

        "title": _extract_title(raw_text),

        "summary": _clean_line(
            sections["about"]
        ),

        "required_skills": required,

        "preferred_skills": preferred,

        "technical_keywords": technical_keywords,

        "experience_requirements": experience_requirements,

        "education_requirements": education_requirements,

        "responsibilities": responsibilities,

        "other_requirements": other_requirements,

        "sections_text": sections,

        "searchable_text": searchable_text,

        "source": {
            "parser": "novus_jd_parser",
            "raw_text": raw_text,
        },

        "stats": {
            "required_count": len(required),
            "preferred_count": len(preferred),
            "technical_keyword_count": len(technical_keywords),
            "experience_requirement_count": len(
                experience_requirements
            ),
            "education_requirement_count": len(
                education_requirements
            ),
            "responsibility_count": len(responsibilities),
            "other_requirement_count": len(other_requirements),
        },
    }