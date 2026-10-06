"""
Novus ATS - Gap Analysis Engine

Transforms ATS matching results into prioritized resume improvement gaps.

This module does not:
- calculate the ATS score
- use AI
- rewrite resume content
- modify Resume Studio state

Its responsibility is to explain:
    what is missing,
    how important it is,
    and where the gap comes from.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Priority configuration
# ---------------------------------------------------------------------------

PRIORITY_LEVELS = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_list(value: Any) -> list:
    """Return a list when the supplied value is actually a list."""
    return value if isinstance(value, list) else []


def _create_gap(
    item: str,
    *,
    category: str,
    priority: str,
    reason: str,
) -> dict[str, str]:
    """
    Create one normalized gap record.
    """
    return {
        "item": item,
        "category": category,
        "priority": priority,
        "reason": reason,
    }


def _sort_gaps(gaps: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Sort gaps from most important to least important.
    """
    return sorted(
        gaps,
        key=lambda gap: (
            -PRIORITY_LEVELS.get(
                gap.get("priority", "low"),
                1,
            ),
            gap.get("item", "").lower(),
        ),
    )


# ---------------------------------------------------------------------------
# Category gap extraction
# ---------------------------------------------------------------------------

def _extract_skill_gaps(
    match_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Extract required and preferred skill gaps.
    """
    gaps: list[dict[str, str]] = []

    required = match_analysis.get(
        "required_skills",
        {},
    )

    for skill in _safe_list(
        required.get("missing")
        if isinstance(required, dict)
        else []
    ):
        gaps.append(
            _create_gap(
                skill,
                category="required_skill",
                priority="critical",
                reason=(
                    "Required by the job description but not "
                    "identified in the resume."
                ),
            )
        )

    preferred = match_analysis.get(
        "preferred_skills",
        {},
    )

    for skill in _safe_list(
        preferred.get("missing")
        if isinstance(preferred, dict)
        else []
    ):
        gaps.append(
            _create_gap(
                skill,
                category="preferred_skill",
                priority="medium",
                reason=(
                    "Preferred by the employer but not identified "
                    "in the resume."
                ),
            )
        )

    return gaps


def _extract_keyword_gaps(
    match_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Extract missing technical keywords.
    """
    gaps: list[dict[str, str]] = []

    technical = match_analysis.get(
        "technical_keywords",
        {},
    )

    for keyword in _safe_list(
        technical.get("missing")
        if isinstance(technical, dict)
        else []
    ):
        gaps.append(
            _create_gap(
                keyword,
                category="technical_keyword",
                priority="high",
                reason=(
                    "Technical keyword appears relevant to the job "
                    "but was not identified in the resume."
                ),
            )
        )

    return gaps


def _extract_responsibility_gaps(
    match_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Extract responsibilities that lack sufficient textual support.
    """
    gaps: list[dict[str, str]] = []

    responsibilities = match_analysis.get(
        "responsibilities",
        {},
    )

    for responsibility in _safe_list(
        responsibilities.get("missing")
        if isinstance(responsibilities, dict)
        else []
    ):
        gaps.append(
            _create_gap(
                responsibility,
                category="responsibility",
                priority="high",
                reason=(
                    "The job responsibility is not sufficiently "
                    "supported by the resume content."
                ),
            )
        )

    return gaps


def _extract_experience_gaps(
    match_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Extract experience-related gaps.
    """
    gaps: list[dict[str, str]] = []

    experience = match_analysis.get(
        "experience",
        {},
    )

    for requirement in _safe_list(
        experience.get("missing")
        if isinstance(experience, dict)
        else []
    ):
        gaps.append(
            _create_gap(
                requirement,
                category="experience",
                priority="critical",
                reason=(
                    "The job description contains an experience "
                    "requirement that was not sufficiently matched."
                ),
            )
        )

    return gaps


def _extract_education_gaps(
    match_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Extract education-related gaps.
    """
    gaps: list[dict[str, str]] = []

    education = match_analysis.get(
        "education",
        {},
    )

    for requirement in _safe_list(
        education.get("missing")
        if isinstance(education, dict)
        else []
    ):
        gaps.append(
            _create_gap(
                requirement,
                category="education",
                priority="critical",
                reason=(
                    "The job description contains an education "
                    "requirement that was not identified in the resume."
                ),
            )
        )

    return gaps


# ---------------------------------------------------------------------------
# Priority adjustment
# ---------------------------------------------------------------------------

def _adjust_duplicate_gaps(
    gaps: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    Avoid treating the same underlying item as several independent gaps.

    For example:
        Docker may appear as both a required skill and technical keyword.

    Both records remain useful, but the primary required-skill gap takes
    precedence.
    """
    priority_by_item: dict[str, int] = {}

    for gap in gaps:
        item = gap["item"].strip().lower()

        current_priority = PRIORITY_LEVELS.get(
            gap["priority"],
            1,
        )

        previous_priority = priority_by_item.get(
            item,
            0,
        )

        priority_by_item[item] = max(
            current_priority,
            previous_priority,
        )

    for gap in gaps:
        item = gap["item"].strip().lower()

        highest_priority = priority_by_item[item]

        for name, value in PRIORITY_LEVELS.items():
            if value == highest_priority:
                gap["priority"] = name
                break

    return gaps


# ---------------------------------------------------------------------------
# Main gap analysis
# ---------------------------------------------------------------------------

def build_gap_analysis(
    match_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a complete prioritized gap analysis.

    Args:
        match_analysis:
            Output from ATS-03 build_match_analysis().

    Returns:
        Structured gap analysis.
    """
    if not isinstance(match_analysis, dict):
        raise ValueError(
            "Match analysis must be a dictionary."
        )

    gaps: list[dict[str, str]] = []

    gaps.extend(
        _extract_skill_gaps(match_analysis)
    )

    gaps.extend(
        _extract_keyword_gaps(match_analysis)
    )

    gaps.extend(
        _extract_responsibility_gaps(match_analysis)
    )

    gaps.extend(
        _extract_experience_gaps(match_analysis)
    )

    gaps.extend(
        _extract_education_gaps(match_analysis)
    )

    gaps = _adjust_duplicate_gaps(gaps)

    gaps = _sort_gaps(gaps)

    # ---------------------------------------------------------------
    # Group gaps by priority
    # ---------------------------------------------------------------

    critical = [
        gap for gap in gaps
        if gap["priority"] == "critical"
    ]

    high = [
        gap for gap in gaps
        if gap["priority"] == "high"
    ]

    medium = [
        gap for gap in gaps
        if gap["priority"] == "medium"
    ]

    low = [
        gap for gap in gaps
        if gap["priority"] == "low"
    ]

    # ---------------------------------------------------------------
    # Group gaps by category
    # ---------------------------------------------------------------

    by_category: dict[str, list[dict[str, str]]] = {}

    for gap in gaps:
        category = gap["category"]

        by_category.setdefault(
            category,
            [],
        ).append(gap)

    return {
        "schema_version": "1.0",

        "gaps": gaps,

        "priority_groups": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
        },

        "by_category": by_category,

        "stats": {
            "total_gaps": len(gaps),
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
        },
    }


# ---------------------------------------------------------------------------
# User-facing recommendations
# ---------------------------------------------------------------------------

def build_gap_summary(
    gap_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a concise summary suitable for the future ATS report UI.
    """
    if not isinstance(gap_analysis, dict):
        raise ValueError(
            "Gap analysis must be a dictionary."
        )

    gaps = _safe_list(
        gap_analysis.get("gaps")
    )

    critical_items = [
        gap["item"]
        for gap in gaps
        if isinstance(gap, dict)
        and gap.get("priority") == "critical"
    ]

    high_items = [
        gap["item"]
        for gap in gaps
        if isinstance(gap, dict)
        and gap.get("priority") == "high"
    ]

    return {
        "total_gaps": len(gaps),

        "top_priority_gaps": (
            critical_items[:5]
            if critical_items
            else high_items[:5]
        ),

        "critical_count": len(critical_items),

        "high_count": len(high_items),

        "has_critical_gaps": bool(
            critical_items
        ),
    }