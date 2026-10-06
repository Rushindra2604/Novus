from __future__ import annotations

import re
from typing import Any


# Common words that should not be treated as meaningful evidence.
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


_GENERIC_DESCRIPTIVE_TERMS = {
    # General resume-writing vocabulary
    "workflow",
    "workflows",
    "pipeline",
    "pipelines",
    "document",
    "documents",
    "content",
    "information",
    "context",
    "structure",
    "clarity",

    # Engineering / development vocabulary
    "engineering",
    "engineer",
    "engineers",
    "technical",
    "technology",
    "technologies",
    "solution",
    "solutions",
    "approach",
    "approaches",
    "method",
    "methods",
    "process",
    "processes",
    "processing",
    "implementation",
    "development",
    "application",
    "applications",
    "system",
    "systems",
    "functionality",
    "function",
    "functions",
    "environment",
    "environments",
    "project",
    "projects",
    "capability",
    "capabilities",

    # Common descriptive language
    "efficient",
    "efficiently",
    "effective",
    "effectively",
    "reliable",
    "reliably",
    "scalable",
    "scalability",
    "robust",
    "optimized",
    "optimization",
    "automated",
    "automatic",
    "professional",
    "impact",
    "quality",
    "performance",
    "experience",
}


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""

    text = text.lower()

    replacements = {
        "react.js": "react",
        "reactjs": "react",
        "node.js": "node",
        "nodejs": "node",
        "postgresql": "postgres",
        "golang": "go",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"[^a-z0-9+#\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _normalize_validator_token(token: str) -> str:
    """
    Normalize simple morphological variations so the validator
    does not flag harmless wording changes as new facts.
    """

    token = token.lower().strip()

    if not token:
        return ""

    replacements = {
        "automated": "automatic",
        "automatically": "automatic",

        "implement": "implement",
        "implemented": "implement",
        "implementing": "implement",
        "implementation": "implement",

        "extract": "extract",
        "extracts": "extract",
        "extracted": "extract",
        "extracting": "extract",
        "extraction": "extract",

        "process": "process",
        "processes": "process",
        "processed": "process",
        "processing": "process",

        "develop": "develop",
        "develops": "develop",
        "developed": "develop",
        "developing": "develop",

        "build": "build",
        "builds": "build",
        "built": "build",
        "building": "build",

        "create": "create",
        "creates": "create",
        "created": "create",
        "creating": "create",

        "design": "design",
        "designs": "design",
        "designed": "design",
        "designing": "design",

        "use": "use",
        "uses": "use",
        "used": "use",
        "using": "use",
        
        "engineer": "engineer",
        "engineered": "engineer",
        "engineering": "engineer",

        "lead": "lead",
        "leads": "lead",
        "led": "lead",
        "leading": "lead",

        "manage": "manage",
        "manages": "manage",
        "managed": "manage",
        "managing": "manage",

        "maintain": "maintain",
        "maintains": "maintain",
        "maintained": "maintain",
        "maintaining": "maintain",

        "improve": "improve",
        "improves": "improve",
        "improved": "improve",
        "improving": "improve",

        "optimize": "optimize",
        "optimizes": "optimize",
        "optimized": "optimize",
        "optimizing": "optimize",

        "integrate": "integrate",
        "integrates": "integrate",
        "integrated": "integrate",
        "integrating": "integrate",
    }

    return replacements.get(token, token)


def _tokens(text: str) -> set[str]:
    tokens = re.findall(
        r"c\+\+|c#|[a-zA-Z0-9]+",
        _normalize_text(text)
    )

    normalized_tokens = set()

    for token in tokens:
        if token in _STOPWORDS:
            continue

        normalized = _normalize_validator_token(token)

        if not normalized:
            continue

        if normalized in _STOPWORDS:
            continue

        normalized_tokens.add(normalized)

    return normalized_tokens


def _extract_numbers(text: str) -> set[str]:
    """Extract numeric claims such as 10%, 500 users, or 3 years."""

    return set(
        re.findall(
            r"\b\d+(?:\.\d+)?%?\b",
            text
        )
    )


def _flatten_resume_evidence(resume: dict[str, Any]) -> str:
    """
    Flatten resume content into text that can be used as evidence.

    This is intentionally conservative. It does not create new facts.
    """

    parts: list[str] = []

    parts.append(str(resume.get("summary", "")))

    skills = resume.get("skills", {})

    if isinstance(skills, dict):
        for values in skills.values():
            if isinstance(values, list):
                parts.extend(str(value) for value in values)
            elif isinstance(values, str):
                parts.append(values)

    for section_name in (
        "experience",
        "projects",
        "certifications",
        "education",
    ):
        section = resume.get(section_name, [])

        if not isinstance(section, list):
            continue

        for item in section:
            if isinstance(item, dict):
                parts.extend(
                    str(value)
                    for value in item.values()
                    if isinstance(value, (str, int, float))
                )
            elif isinstance(item, str):
                parts.append(item)

    return " ".join(parts)


def find_unsupported_keywords(
    original: str,
    rewritten: str,
    *,
    resume_context: dict[str, Any] | None = None,
) -> list[str]:
    """
    Find meaningful terms appearing in the rewrite that are not
    supported by the original content or supplied resume evidence.

    Generic resume-writing vocabulary is ignored because wording
    improvements naturally introduce terms such as "workflow",
    "pipeline", "efficiently", and "engineering".

    The validator remains conservative for technical terms,
    technologies, tools, and other potentially factual additions.
    """

    original_tokens = _tokens(original)

    evidence_text = _flatten_resume_evidence(
        resume_context or {}
    )

    evidence_tokens = _tokens(evidence_text)

    supported_tokens = (
        original_tokens |
        evidence_tokens
    )

    rewritten_tokens = _tokens(rewritten)

    unsupported = rewritten_tokens - supported_tokens

    meaningful_unsupported = {
        token
        for token in unsupported
        if token not in _GENERIC_DESCRIPTIVE_TERMS
    }

    return sorted(meaningful_unsupported)


def find_new_numeric_claims(
    original: str,
    rewritten: str,
) -> list[str]:
    """Find numerical claims added by the AI."""

    original_numbers = _extract_numbers(original)
    rewritten_numbers = _extract_numbers(rewritten)

    return sorted(rewritten_numbers - original_numbers)


def validate_rewrite(
    *,
    original: str,
    rewritten: str,
    resume_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Validate an AI-generated rewrite.

    The validator does not silently modify the AI output.
    It reports whether the suggestion should be trusted.
    """

    if not isinstance(original, str) or not original.strip():
        raise ValueError("Original content cannot be empty.")

    if not isinstance(rewritten, str) or not rewritten.strip():
        raise ValueError("Rewritten content cannot be empty.")

    unsupported_keywords = find_unsupported_keywords(
        original,
        rewritten,
        resume_context=resume_context,
    )

    new_numeric_claims = find_new_numeric_claims(
        original,
        rewritten,
    )

    warnings: list[str] = []

    if unsupported_keywords:
        warnings.append(
            "The rewrite contains terms that are not clearly "
            "supported by the supplied resume evidence."
        )

    if new_numeric_claims:
        warnings.append(
            "The rewrite contains numerical claims that were not "
            "present in the original content."
        )

    is_safe = not warnings

    return {
        "is_safe": is_safe,
        "warnings": warnings,
        "unsupported_keywords": unsupported_keywords,
        "new_numeric_claims": new_numeric_claims,
    }