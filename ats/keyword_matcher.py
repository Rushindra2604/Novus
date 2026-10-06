"""
Novus ATS - Keyword and Skill Matching Engine

Compares a normalized resume against a normalized job description.

This module does not:
- calculate an ATS score
- use AI
- rewrite resume content
- modify Resume Studio state

Its responsibility is only to identify matches and gaps.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _normalize_term(value: str) -> str:
    """
    Normalize a skill/keyword for comparison.

    Examples:
        'Python'       -> 'python'
        'React.js'     -> 'react'
        'Node.js'      -> 'node'
        'PostgreSQL'   -> 'postgresql'
        'C++'          -> 'c++'
    """

    if not isinstance(value, str):
        return ""

    value = value.strip().lower()

    # Normalize common technology aliases.
    aliases = {
        "react.js": "react",
        "reactjs": "react",

        "html5": "html",
        "html 5": "html",
        "css3": "css",
        "css 3": "css",

        "node.js": "node",
        "nodejs": "node",

        "vue.js": "vue",
        "vuejs": "vue",

        "nextjs": "next.js",

        "postgres": "postgresql",
        "postgres db": "postgresql",

        "mongodb database": "mongodb",

        "golang": "go",

        "c sharp": "c#",
        "c-sharp": "c#",

        "cplusplus": "c++",
        "cpp": "c++",

        "javascript": "javascript",
        "js": "javascript",

        "typescript": "typescript",
        "ts": "typescript",

        "python3": "python",

        "amazon web services": "aws",

        "google cloud platform": "gcp",

        "microsoft azure": "azure",

        "structured query language": "sql",

        "restful api": "rest api",
        "rest apis": "rest api",
    }

    return aliases.get(value, value)


def _deduplicate(values: list[str]) -> list[str]:
    """
    Deduplicate while preserving order.
    """

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = value.strip()

        if not cleaned:
            continue

        normalized = _normalize_term(cleaned)

        if normalized not in seen:
            seen.add(normalized)
            result.append(cleaned)

    return result


def _normalize_list(values: Any) -> list[str]:
    """
    Safely convert a value into a list of strings.
    """

    if not isinstance(values, list):
        return []

    return _deduplicate(
        [
            value
            for value in values
            if isinstance(value, str) and value.strip()
        ]
    )


# ---------------------------------------------------------------------------
# Directional skill evidence relationships
# ---------------------------------------------------------------------------

# These relationships are intentionally directional.
#
# Example:
#   JD requires SQL
#   Resume contains MySQL
#   -> SQL requirement can be supported by MySQL experience.
#
# But:
#   JD requires MySQL
#   Resume contains SQL
#   -> NOT automatically supported.
#
# This prevents broad skills from falsely proving specific technologies.

SKILL_EVIDENCE_RELATIONSHIPS: dict[str, set[str]] = {
    "sql": {
        "mysql",
        "postgresql",
        "postgres",
        "sqlite",
        "mariadb",
        "sql server",
        "oracle",
    },

    "ai": {
        "gemini",
        "google gemini",
        "google gemini api",
        "openai",
        "openai api",
        "anthropic",
        "claude",
    },

    "ai api": {
        "gemini",
        "google gemini",
        "google gemini api",
        "openai",
        "openai api",
        "anthropic",
        "claude",
    },

    "ai apis": {
        "gemini",
        "google gemini",
        "google gemini api",
        "openai",
        "openai api",
        "anthropic",
        "claude",
    },

    # A resume explicitly showing REST APIs / RESTful APIs is
    # evidence for a generic API requirement. The reverse is
    # intentionally not assumed.
    "api": {
        "rest api",
        "restful api",
        "rest apis",
        "graphql",
        "graphql api",
        "web api",
    },

    "apis": {
        "rest api",
        "restful api",
        "rest apis",
        "graphql",
        "graphql api",
        "web api",
    },

    "pdf parsing": {
        "pdfplumber",
        "pypdf",
        "pymupdf",
        "fitz",
    },

    "pdf processing": {
        "pdfplumber",
        "pypdf",
        "pymupdf",
        "fitz",
    },

    "cloud deployment": {
        "render",
        "pythonanywhere",
        "vercel",
        "netlify",
        "heroku",
    },

    "application deployment": {
        "render",
        "pythonanywhere",
        "vercel",
        "netlify",
        "heroku",
    },
}


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _terms_match(left: str, right: str) -> bool:
    """
    Determine whether two terms represent the same normalized concept.
    """

    left_normalized = _normalize_term(left)
    right_normalized = _normalize_term(right)

    if not left_normalized or not right_normalized:
        return False

    return left_normalized == right_normalized


def _contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Determine whether a normalized phrase appears inside normalized text.

    This works with multi-word phrases such as:

        'ai apis'
        'pdf parsing'
        'application deployment'
    """

    text_tokens = _tokenize(text)
    phrase_tokens = _tokenize(phrase)

    if not text_tokens or not phrase_tokens:
        return False

    return phrase_tokens.issubset(text_tokens)


def _term_has_evidence(
    jd_term: str,
    resume_terms: list[str],
    resume_text: str = "",
) -> bool:
    """
    Determine whether a JD term is supported by explicit resume evidence.

    Matching order:

    1. Exact normalized skill match.
    2. Directional skill-evidence relationship.
       This also works when the JD term is a full sentence.
    3. Evidence phrase found in the resume text.

    Examples:

        JD:  SQL
        Resume: MySQL
        -> supported

        JD:  Experience with PDF parsing.
        Resume: PDFPlumber
        -> supported

        JD:  Familiarity with AI APIs.
        Resume: Google Gemini API
        -> supported

        JD:  Experience deploying applications on Render.
        Resume: Render
        -> supported

    The relationship is intentionally directional so that broad skills
    cannot automatically prove specific technologies.
    """

    jd_normalized = _normalize_term(jd_term)

    if not jd_normalized:
        return False

    # ---------------------------------------------------------------
    # 1. Exact match
    # ---------------------------------------------------------------

    if any(
        _terms_match(jd_term, resume_term)
        for resume_term in resume_terms
    ):
        return True

    # ---------------------------------------------------------------
    # 2. Directional evidence relationship
    # ---------------------------------------------------------------

    normalized_resume_terms = {
        _normalize_term(term)
        for term in resume_terms
        if isinstance(term, str)
    }

    for relationship_name, evidence_terms in (
        SKILL_EVIDENCE_RELATIONSHIPS.items()
    ):
        # Important improvement:
        #
        # The JD parser can return either:
        #
        #   "PDF parsing"
        #
        # or:
        #
        #   "Experience with PDF parsing."
        #
        # So we don't require the complete JD term to equal
        # the relationship name.
        relationship_matches_jd = (
            _normalize_term(relationship_name) == jd_normalized
            or _contains_phrase(
                jd_normalized,
                relationship_name,
            )
        )

        # Also allow a specific technology/platform mentioned
        # directly inside the JD requirement sentence.
        #
        # Example:
        #   "Experience deploying applications on Render or PythonAnywhere."
        #
        # The relationship name "cloud deployment" is not literally
        # present, but "Render" and "PythonAnywhere" are.
        if not relationship_matches_jd:
            relationship_matches_jd = any(
                _contains_phrase(
                    jd_normalized,
                    evidence_term,
                )
                for evidence_term in evidence_terms
            )

        if not relationship_matches_jd:
            continue

        # Check explicit resume skill entries first.
        for evidence_term in evidence_terms:
            normalized_evidence = _normalize_term(evidence_term)

            if normalized_evidence in normalized_resume_terms:
                return True

    # ---------------------------------------------------------------
    # 3. Search full resume text
    # ---------------------------------------------------------------

    if isinstance(resume_text, str) and resume_text.strip():
        resume_tokens = _tokenize(resume_text)

        for relationship_name, evidence_terms in (
            SKILL_EVIDENCE_RELATIONSHIPS.items()
        ):
            relationship_matches_jd = (
                _normalize_term(relationship_name) == jd_normalized
                or _contains_phrase(
                    jd_normalized,
                    relationship_name,
                )
            )

            if not relationship_matches_jd:
                relationship_matches_jd = any(
                    _contains_phrase(
                        jd_normalized,
                        evidence_term,
                    )
                    for evidence_term in evidence_terms
                )

            if not relationship_matches_jd:
                continue

            for evidence_term in evidence_terms:
                evidence_tokens = _tokenize(evidence_term)

                if (
                    evidence_tokens
                    and evidence_tokens.issubset(resume_tokens)
                ):
                    return True

    return False


def match_terms(
    resume_terms: list[str],
    jd_terms: list[str],
    *,
    resume_text: str = "",
) -> dict[str, list[str]]:
    """
    Match resume terms against JD terms.

    Returns:

        {
            "matched": [...],
            "missing": [...]
        }

    The original JD spelling is preserved in the output.
    """

    resume_terms = _normalize_list(resume_terms)
    jd_terms = _normalize_list(jd_terms)

    matched: list[str] = []
    missing: list[str] = []

    for jd_term in jd_terms:
        if _term_has_evidence(
            jd_term,
            resume_terms,
            resume_text,
        ):
            matched.append(jd_term)
        else:
            missing.append(jd_term)

    return {
        "matched": matched,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# Requirement text matching
# ---------------------------------------------------------------------------

def _normalize_token(token: str) -> str:
    """
    Normalize a single word for lightweight textual matching.

    This handles common grammatical variations so that resume wording such
    as "developed" can match JD wording such as "develop".
    """

    token = token.lower().strip()

    if not token:
        return ""

    # Preserve important technology tokens.
    if token in {
        "c++",
        "c#",
        "node.js",
        "react.js",
        "next.js",
    }:
        return token

    # Common irregular verbs.
    irregular = {
        "built": "build",
        "broke": "break",
        "bought": "buy",
        "came": "come",
        "created": "create",
        "did": "do",
        "developed": "develop",
        "designed": "design",
        "debugged": "debug",
        "deployed": "deploy",
        "drove": "drive",
        "found": "find",
        "gave": "give",
        "grew": "grow",
        "had": "have",
        "implemented": "implement",
        "improved": "improve",
        "integrated": "integrate",
        "led": "lead",
        "maintained": "maintain",
        "managed": "manage",
        "ran": "run",
        "saw": "see",
        "sent": "send",
        "set": "set",
        "solved": "solve",
        "spoke": "speak",
        "tested": "test",
        "used": "use",
        "wrote": "write",
    }

    if token in irregular:
        return irregular[token]

    # Common English suffixes.
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]

    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]

    if len(token) > 4 and token.endswith("es"):
        return token[:-2]

    if len(token) > 3 and token.endswith("s"):
        return token[:-1]

    return token


def _tokenize(text: str) -> set[str]:
    """
    Create a normalized token set from text.

    This is used only for lightweight textual matching. It is not an ATS
    score and does not perform semantic AI matching.
    """

    if not isinstance(text, str):
        return set()

    raw_tokens = re.findall(
        r"c\+\+|c#|[a-zA-Z0-9]+",
        text.lower(),
    )

    tokens = {
        _normalize_token(token)
        for token in raw_tokens
    }

    return {
        token
        for token in tokens
        if len(token) > 1
    }


def _text_overlap(left: str, right: str) -> float:
    """
    Calculate how much of the target text is supported by the source text.

    The left side is the target requirement/responsibility.
    The right side is the resume evidence.

    The returned value represents the proportion of target tokens
    that are supported by the source text.

    This is intentionally NOT an ATS score.
    """

    target_tokens = _tokenize(left)
    source_tokens = _tokenize(right)

    if not target_tokens or not source_tokens:
        return 0.0

    intersection = target_tokens & source_tokens

    return len(intersection) / len(target_tokens)


def match_responsibilities(
    resume_text: str,
    responsibilities: list[str],
    *,
    threshold: float = 0.20,
) -> dict[str, list[str]]:
    """
    Identify responsibilities that have textual support in the resume.

    A responsibility is considered supported when at least `threshold`
    of its tokens appear in the resume.

    This is deliberately conservative and deterministic.
    """

    matched: list[str] = []
    missing: list[str] = []

    if not isinstance(resume_text, str):
        resume_text = ""

    for responsibility in _normalize_list(responsibilities):
        overlap = _text_overlap(
            responsibility,
            resume_text,
        )

        if overlap >= threshold:
            matched.append(responsibility)
        else:
            missing.append(responsibility)

    return {
        "matched": matched,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# Main matching engine
# ---------------------------------------------------------------------------

def build_match_analysis(
    resume_analysis: dict[str, Any],
    jd_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare normalized resume analysis against normalized JD analysis.

    Expected inputs are the outputs of:

        ats.resume_analyzer.build_resume_analysis()
        ats.jd_parser.parse_job_description()

    Returns a structured matching result suitable for ATS-04 scoring.
    """

    if not isinstance(resume_analysis, dict):
        raise ValueError("Resume analysis must be a dictionary.")

    if not isinstance(jd_analysis, dict):
        raise ValueError("Job description analysis must be a dictionary.")

    # ------------------------------------------------------------------
    # Resume searchable text
    # ------------------------------------------------------------------

    resume_searchable_text = resume_analysis.get(
        "searchable_text",
        "",
    )

    if not isinstance(resume_searchable_text, str):
        resume_searchable_text = ""

    # ------------------------------------------------------------------
    # Resume skills
    # ------------------------------------------------------------------

    resume_skills: list[str] = []

    skills = resume_analysis.get("skills", {})

    if isinstance(skills, dict):
        for category_values in skills.values():
            if isinstance(category_values, list):
                resume_skills.extend(category_values)

    resume_skills = _normalize_list(resume_skills)

    # ------------------------------------------------------------------
    # Required skills
    # ------------------------------------------------------------------

    required_skills = _normalize_list(
        jd_analysis.get("required_skills", [])
    )

    required_match = match_terms(
        resume_skills,
        required_skills,
        resume_text=resume_searchable_text,
    )

    # ------------------------------------------------------------------
    # Preferred skills
    # ------------------------------------------------------------------

    preferred_skills = _normalize_list(
        jd_analysis.get("preferred_skills", [])
    )

    preferred_match = match_terms(
        resume_skills,
        preferred_skills,
        resume_text=resume_searchable_text,
    )

    # ------------------------------------------------------------------
    # Technical keywords
    # ------------------------------------------------------------------

    technical_keywords = _normalize_list(
        jd_analysis.get("technical_keywords", [])
    )

    # Use both explicit resume skills and resume searchable text.
    keyword_resume_terms = resume_skills.copy()

    resume_tokens = _tokenize(resume_searchable_text)

    for keyword in technical_keywords:
        normalized_keyword = _normalize_term(keyword)

        if normalized_keyword in resume_tokens:
            keyword_resume_terms.append(keyword)

    technical_match = match_terms(
        keyword_resume_terms,
        technical_keywords,
        resume_text=resume_searchable_text,
    )

    # ------------------------------------------------------------------
    # Responsibilities
    # ------------------------------------------------------------------

    responsibility_match = match_responsibilities(
        resume_searchable_text,
        jd_analysis.get("responsibilities", []),
    )

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    resume_education_text = " ".join(
        [
            str(item)
            for item in resume_analysis.get("education", [])
            if isinstance(item, (str, dict))
        ]
    )

    education_requirements = _normalize_list(
        jd_analysis.get("education_requirements", [])
    )

    education_match = match_responsibilities(
        resume_education_text,
        education_requirements,
        threshold=0.20,
    )

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    resume_experience = resume_analysis.get(
        "experience",
        [],
    )

    resume_experience_text = " ".join(
        [
            str(item)
            for item in resume_experience
            if isinstance(item, (str, dict))
        ]
    )

    experience_requirements = _normalize_list(
        jd_analysis.get("experience_requirements", [])
    )

    experience_match = match_responsibilities(
        resume_experience_text,
        experience_requirements,
        threshold=0.20,
    )

    # ------------------------------------------------------------------
    # Overall result
    # ------------------------------------------------------------------

    return {
        "schema_version": "1.0",

        "required_skills": {
            "matched": required_match["matched"],
            "missing": required_match["missing"],
        },

        "preferred_skills": {
            "matched": preferred_match["matched"],
            "missing": preferred_match["missing"],
        },

        "technical_keywords": {
            "matched": technical_match["matched"],
            "missing": technical_match["missing"],
        },

        "responsibilities": {
            "matched": responsibility_match["matched"],
            "missing": responsibility_match["missing"],
        },

        "education": {
            "matched": education_match["matched"],
            "missing": education_match["missing"],
        },

        "experience": {
            "matched": experience_match["matched"],
            "missing": experience_match["missing"],
        },

        "stats": {
            "required_matched": len(
                required_match["matched"]
            ),
            "required_missing": len(
                required_match["missing"]
            ),

            "preferred_matched": len(
                preferred_match["matched"]
            ),
            "preferred_missing": len(
                preferred_match["missing"]
            ),

            "technical_keywords_matched": len(
                technical_match["matched"]
            ),
            "technical_keywords_missing": len(
                technical_match["missing"]
            ),

            "responsibilities_matched": len(
                responsibility_match["matched"]
            ),
            "responsibilities_missing": len(
                responsibility_match["missing"]
            ),

            "education_matched": len(
                education_match["matched"]
            ),
            "education_missing": len(
                education_match["missing"]
            ),

            "experience_matched": len(
                experience_match["matched"]
            ),
            "experience_missing": len(
                experience_match["missing"]
            ),
        },
    }