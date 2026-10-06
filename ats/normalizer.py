"""Normalize a parsed Novus Resume Studio state for ATS analysis.

The normalizer creates an analysis-safe representation without changing
Resume Studio's existing state or UI data.
"""

from __future__ import annotations

import re
from typing import Any


_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w+#.\-/]+")


def normalize_text(value: Any) -> str:
    """Return consistent searchable text while preserving useful tech tokens."""
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def normalize_term(value: Any) -> str:
    """Normalize a skill/keyword for matching without destroying tech names."""
    text = normalize_text(value).lower()
    text = text.replace("c sharp", "c#").replace("c plus plus", "c++")
    text = _PUNCT_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _list_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [normalize_text(item) for item in value if normalize_text(item)]


def _join(values: list[str]) -> str:
    return " ".join(v for v in values if v)


def normalize_resume_state(state: dict[str, Any] | None) -> dict[str, Any]:
    """Build the canonical ATS resume representation.

    The returned object is separate from ResumeEngine.state, so ATS processing
    cannot accidentally mutate Resume Studio data.
    """
    state = state or {}
    personal = state.get("personal") or {}
    skills = state.get("skills") or {}

    education = []
    for item in state.get("education") or []:
        if not isinstance(item, dict):
            continue
        education.append({
            "degree": normalize_text(item.get("degree")),
            "institution": normalize_text(item.get("institution")),
            "location": normalize_text(item.get("location")),
            "start_year": normalize_text(item.get("startYear")),
            "end_year": normalize_text(item.get("endYear")),
            "score": normalize_text(item.get("score")),
            "description": normalize_text(item.get("description")),
        })

    experience = []
    for item in state.get("experience") or []:
        if not isinstance(item, dict):
            continue
        responsibilities = _list_values(
            item.get("responsibilities", item.get("description", []))
        )
        experience.append({
            "job_title": normalize_text(
                item.get("jobTitle", item.get("title"))
            ),
            "company": normalize_text(item.get("company")),
            "location": normalize_text(item.get("location")),
            "start_date": normalize_text(
                item.get("startDate", item.get("start"))
            ),
            "end_date": normalize_text(
                item.get("endDate", item.get("end"))
            ),
            "responsibilities": responsibilities,
        })

    projects = []
    for item in state.get("projects") or []:
        if not isinstance(item, dict):
            continue
        bullets = _list_values(item.get("bullets"))
        technologies = _list_values(item.get("technologies"))
        projects.append({
            "title": normalize_text(item.get("title")),
            "technologies": technologies,
            "bullets": bullets,
            "github": normalize_text(item.get("github")),
            "live_demo": normalize_text(
                item.get("liveDemo", item.get("live_demo"))
            ),
        })

    certifications = []
    for item in state.get("certifications") or []:
        if not isinstance(item, dict):
            continue
        certifications.append({
            "name": normalize_text(item.get("name")),
            "organization": normalize_text(item.get("organization")),
            "month": normalize_text(item.get("month")),
            "year": normalize_text(item.get("year")),
            "credential_id": normalize_text(item.get("credentialId")),
            "credential_url": normalize_text(item.get("credentialUrl")),
        })

    additional_sections = []
    for item in state.get("additionalSections") or []:
        if not isinstance(item, dict):
            continue
        additional_sections.append({
            "title": normalize_text(item.get("title")),
            "content": normalize_text(
                item.get("content", item.get("description", ""))
            ),
        })

    skill_groups = {
        "languages": _list_values(skills.get("languages")),
        "frameworks": _list_values(skills.get("frameworks")),
        "databases": _list_values(skills.get("databases")),
        "tools": _list_values(skills.get("tools")),
        "others": _list_values(skills.get("others")),
    }

    all_skill_names = []
    for values in skill_groups.values():
        all_skill_names.extend(values)

    summary = normalize_text(state.get("summary"))
    headline = normalize_text(personal.get("headline"))

    # Build searchable content from structured fields. This is deliberately
    # separate from any later keyword extraction/matching rules.
    sections = {
        "summary": summary,
        "skills": _join(all_skill_names),
        "experience": _join([
            _join([
                item["job_title"],
                item["company"],
                item["location"],
                *item["responsibilities"],
            ])
            for item in experience
        ]),
        "projects": _join([
            _join([
                item["title"],
                *item["technologies"],
                *item["bullets"],
            ])
            for item in projects
        ]),
        "education": _join([
            _join([
                item["degree"],
                item["institution"],
                item["location"],
                item["description"],
            ])
            for item in education
        ]),
        "certifications": _join([
            _join([item["name"], item["organization"]])
            for item in certifications
        ]),
        "additional": _join([
            _join([item["title"], item["content"]])
            for item in additional_sections
        ]),
    }

    searchable_text = _join([
        headline,
        *sections.values(),
    ])

    return {
        "schema_version": "1.0",
        "title": normalize_text(state.get("title")),
        "personal": {
            "full_name": normalize_text(personal.get("fullName")),
            "headline": headline,
            "email": normalize_text(personal.get("email")),
            "phone": normalize_text(personal.get("phone")),
            "location": normalize_text(personal.get("location")),
            "linkedin": normalize_text(personal.get("linkedin")),
            "github": normalize_text(personal.get("github")),
            "portfolio": normalize_text(personal.get("portfolio")),
        },
        "summary": summary,
        "skills": skill_groups,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "additional_sections": additional_sections,
        "sections_text": sections,
        "searchable_text": searchable_text,
        "stats": {
            "skill_count": len({
                normalize_term(v)
                for v in all_skill_names
                if normalize_term(v)
            }),
            "education_count": len(education),
            "experience_count": len(experience),
            "project_count": len(projects),
            "certification_count": len(certifications),
            "additional_section_count": len(additional_sections),
            "word_count": len(searchable_text.split()),
        },
    }
