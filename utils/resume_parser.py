"""
Novus Resume Parser
-------------------
Local/deterministic parser for PDF/DOCX extracted resume text.

The parser deliberately returns the same state shape used by Resume Studio.
It does not call an AI service and does not invent missing information.

Future AI parsing can use the same parse_resume(text) interface/output shape.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_resume(text: str, fallback_title: str = "Untitled Resume") -> dict:
    """
    Convert extracted resume text into the Resume Studio state structure.

    Returns:
        {
            "title": str,
            "personal": {...},
            "summary": str,
            "education": [...],
            "skills": {...},
            "projects": [...],
            "experience": [...],
            "certifications": [...],
            "additionalSections": [...]
        }
    """
    lines = _clean_lines(text)

    state = _empty_state(fallback_title)

    if not lines:
        return state

    state["personal"] = _parse_personal(lines)

    sections = _split_sections(lines)

    state["summary"] = _parse_summary(sections)
    state["education"] = _parse_education(sections.get("education", []))
    state["skills"] = _parse_skills(sections.get("skills", []))
    state["projects"] = _parse_projects(sections.get("projects", []))
    state["experience"] = _parse_experience(sections.get("experience", []))
    state["certifications"] = _parse_certifications(sections.get("certifications", []))

    # Preserve user-created/unknown sections rather than silently throwing
    # them away. They can later be shown/edited as additional sections.
    state["additionalSections"] = _parse_additional_sections(
        sections,
        known={
            "personal",
            "summary",
            "education",
            "skills",
            "projects",
            "experience",
            "certifications",
        },
    )

    # Prefer the parsed name as the title only when a useful name exists.
    if state["personal"].get("fullName"):
        state["title"] = state["personal"]["fullName"]
    else:
        state["title"] = fallback_title or "Imported Resume"

    return state


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _empty_state(title: str) -> dict:
    return {
        "title": title or "Untitled Resume",
        "personal": {
            "fullName": "",
            "headline": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "github": "",
            "portfolio": "",
        },
        "summary": "",
        "education": [],
        "skills": {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "tools": [],
            "others": [],
        },
        "projects": [],
        "experience": [],
        "certifications": [],
        "additionalSections": [],
    }


# ---------------------------------------------------------------------------
# Cleaning / normalization
# ---------------------------------------------------------------------------

def _clean_lines(text: str) -> List[str]:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")

    # Normalize common PDF/DOCX bullet characters.
    text = re.sub(r"[•●▪◦‣⁃·]", "•", text)

    cleaned = []

    for raw in text.split("\n"):
        line = re.sub(r"\s+", " ", raw).strip()

        if not line:
            continue

        # Remove decorative separators.
        if re.fullmatch(r"[-_=~*·.]{3,}", line):
            continue

        # Fix common PDF extraction word-spacing artifacts.
        line = re.sub(r"\bF\s+rontend\b", "Frontend", line, flags=re.I)
        line = re.sub(r"\bT\s+ools\b", "Tools", line, flags=re.I)
        line = re.sub(r"\bT\s+echnology\b", "Technology", line, flags=re.I)
        line = re.sub(r"\bT\s+echnologies\b", "Technologies", line, flags=re.I)

        # Separate words accidentally joined to a year.
        line = re.sub(r"([A-Za-z])((?:19|20)\d{2})\b", r"\1 \2", line)

        # Remove standalone page numbers.
        if re.fullmatch(r"\d{1,3}", line):
            continue

        cleaned.append(line)

    return cleaned


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

_SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "career summary",
        "objective",
        "career objective",
        "about me",
        "about",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
        "career history",
        "internship experience",
        "internships",
        "internship",
        "intern",
    },
    "education": {
        "education",
        "educational background",
        "academic background",
        "academic qualifications",
        "qualifications",
        "education & qualifications",
    },
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technical expertise",
        "technologies",
        "technical proficiencies",
        "skills & technologies",
    },
    "projects": {
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "selected projects",
        "project experience",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses & certifications",
        "licenses and certifications",
        "professional certifications",
    },
    "personal": {
        "personal information",
        "contact",
        "contact information",
        "profile",
    },
}

# These are headings that should not accidentally become content.
_GENERIC_HEADING_WORDS = {
    "resume",
    "curriculum vitae",
    "cv",
    "vitae",
}


def _normalize_heading(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[:|•]+$", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _detect_section(line: str) -> str | None:
    normalized = _normalize_heading(line)

    # Normal heading match.
    for section, aliases in _SECTION_ALIASES.items():
        if normalized in aliases:
            return section

    # PDF-safe heading match.
    #
    # Some PDF extractors insert spaces inside words:
    #   "Cer Tifica Tes" -> "certificates"
    #   "Pro Jects" -> "projects"
    #
    # Only use this compact form for matching known section headings.
    # We do NOT modify the actual resume content.
    compact_normalized = re.sub(r"\s+", "", normalized)

    for section, aliases in _SECTION_ALIASES.items():
        compact_aliases = {
            re.sub(r"\s+", "", alias)
            for alias in aliases
        }

        if compact_normalized in compact_aliases:
            return section

    # Support headings such as "TECHNICAL SKILLS:".
    if normalized.endswith(":"):
        normalized = normalized[:-1].strip()

        for section, aliases in _SECTION_ALIASES.items():
            if normalized in aliases:
                return section

    return None


def _looks_like_heading(line: str) -> bool:
    """
    Detect unknown/custom resume section headings.

    Only recognize a line as a custom heading when there is strong
    evidence that it is actually a section name.

    Normal resume content such as:
        B.Tech
        HTML
        Python
        Resume Builder
        Computer Science and Engineering

    must remain content.
    """

    value = line.strip()

    if not value:
        return False

    # Known sections are already handled by _detect_section().
    if _detect_section(value):
        return True

    # Never treat bullets as headings.
    if value.startswith(("•", "-", "–", "—", "▪", "◦", "‣", "⁃")):
        return False

    # Contact information is never a heading.
    if _EMAIL_RE.search(value):
        return False

    if _PHONE_RE.search(value):
        return False

    if _URL_RE.search(value):
        return False

    # Dates are never headings.
    if re.search(r"\b(?:19|20)\d{2}\b", value):
        return False

    # Common technology / academic content that may appear in ALL CAPS.
    content_words = {
        "html",
        "css",
        "js",
        "javascript",
        "typescript",
        "python",
        "java",
        "c",
        "c++",
        "c#",
        "sql",
        "mysql",
        "mongodb",
        "react",
        "flask",
        "django",
        "node",
        "nodejs",
        "api",
        "aws",
        "azure",
        "gcp",
        "git",
        "github",
        "docker",
        "kubernetes",
        "b.tech",
        "btech",
        "m.tech",
        "mtech",
        "mba",
        "mca",
        "phd",
    }

    normalized = _normalize_heading(value)

    if normalized in content_words:
        return False

    # Strongly recognize common custom section names.
    custom_section_words = {
        "achievements",
        "awards",
        "honors",
        "interests",
        "hobbies",
        "languages",
        "publications",
        "volunteering",
        "volunteer experience",
        "activities",
        "extracurricular activities",
        "leadership",
        "references",
        "strengths",
        "declaration",
        "personal details",
        "additional information",
        "additional details",
    }

    if normalized in custom_section_words:
        return True

    # ALL-CAPS unknown headings are allowed only when they contain
    # multiple words. This prevents HTML, CSS, SQL, etc. from becoming
    # headings.
    letters = re.sub(r"[^A-Za-z]", "", value)

    if (
        len(letters) >= 6
        and value.upper() == value
        and len(value.split()) >= 2
        and len(value.split()) <= 5
    ):
        return True

    return False


def _split_sections(lines: List[str]) -> Dict[str, List[str]]:
    """
    Split the document into recognized sections.

    Unknown headings are retained under their heading text so they can become
    additional sections later.
    """
    sections: Dict[str, List[str]] = {}
    current = "header"
    sections[current] = []

    for line in lines:
        detected = _detect_section(line)

        if detected:
            current = detected
            sections.setdefault(current, [])
            continue

        # Treat unknown all-caps/title headings as additional section names,
        # but avoid interpreting normal short header lines as headings.
        if _looks_like_heading(line) and current != "header":
            heading = _normalize_heading(line)
            if heading not in sections and len(heading.split()) <= 5:
                current = f"custom:{heading}"
                sections.setdefault(current, [])
                continue

        sections.setdefault(current, []).append(line)

    return sections


# ---------------------------------------------------------------------------
# Personal information
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.I,
)

_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
)

_URL_RE = re.compile(
    r"(https?://|www\.)[^\s]+",
    re.I,
)

_LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s|]+",
    re.I,
)

_GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[^\s|]+",
    re.I,
)


def _strip_contact_tokens(line: str) -> str:
    value = _EMAIL_RE.sub("", line)
    value = _PHONE_RE.sub("", value)
    value = _LINKEDIN_RE.sub("", value)
    value = _GITHUB_RE.sub("", value)
    value = _URL_RE.sub("", value)
    value = re.sub(r"[|•·,;]+", " ", value)
    return re.sub(r"\s+", " ", value).strip(" -")


def _clean_url(value: str) -> str:
    return value.rstrip(".,;)]}")


def _parse_personal(lines: List[str]) -> dict:
    personal = _empty_state("")["personal"]

    # Only inspect the beginning of the resume for contact information.
    header = lines[:20]

    email_match = _EMAIL_RE.search("\n".join(header))
    if email_match:
        personal["email"] = email_match.group(0).strip()

    phone_match = _find_phone(header)
    if phone_match:
        personal["phone"] = phone_match

    linkedin_match = _LINKEDIN_RE.search("\n".join(header))
    if linkedin_match:
        personal["linkedin"] = _clean_url(linkedin_match.group(0))

    github_match = _GITHUB_RE.search("\n".join(header))
    if github_match:
        personal["github"] = _clean_url(github_match.group(0))

    # A non-social URL near the top is treated as portfolio.
    for line in header:
        for match in _URL_RE.findall(line):
            pass

        urls = re.findall(r"(?:https?://|www\.)[^\s|]+", line, re.I)
        for url in urls:
            url = _clean_url(url)
            if "linkedin.com" in url.lower() or "github.com" in url.lower():
                continue
            personal["portfolio"] = url
            break
        if personal["portfolio"]:
            break

    # Name is normally the first meaningful non-contact line.
    candidates = []
    for line in header[:8]:
        if _detect_section(line):
            break

        if (
            _EMAIL_RE.search(line)
            or _PHONE_RE.search(line)
            or _URL_RE.search(line)
            or "|" in line
        ):
            continue

        if line.lower() in _GENERIC_HEADING_WORDS:
            continue

        if len(line.split()) <= 6 and len(line) <= 60:
            candidates.append(line)

    if candidates:
        personal["fullName"] = _clean_name(candidates[0])

        # Headline is usually the next short descriptive line.
        if len(candidates) > 1:
            headline = candidates[1]
            if (
                headline != personal["fullName"]
                and not _looks_like_heading(headline)
            ):
                personal["headline"] = headline

    # Location: look for a line containing common geographic separators,
    # or a contact line fragment after removing known tokens.
    if not personal["location"]:
        for line in header[:10]:
            fragment = _strip_contact_tokens(line)

            if not fragment or fragment == personal["fullName"]:
                continue

            if _looks_like_location(fragment):
                personal["location"] = fragment
                break

    return personal


def _find_phone(lines: List[str]) -> str:
    for line in lines:
        match = _PHONE_RE.search(line)
        if match:
            value = match.group(0).strip()
            digits = re.sub(r"\D", "", value)

            # Avoid treating years or tiny numeric strings as phone numbers.
            if 8 <= len(digits) <= 15:
                return value

    return ""


def _clean_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" -|•")
    return value


def _looks_like_location(value: str) -> bool:
    lower = value.lower()

    if any(token in lower for token in (
        "linkedin",
        "github",
        "http://",
        "https://",
        "@",
    )):
        return False

    if re.search(r"\b(india|usa|uk|canada|australia|uae|singapore)\b", lower):
        return True

    if "," in value and len(value.split()) <= 8:
        return True

    return False


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _parse_summary(sections: Dict[str, List[str]]) -> str:
    values = sections.get("summary", [])
    if not values:
        return ""

    return " ".join(
        _strip_bullet(line)
        for line in values
        if _strip_bullet(line)
    ).strip()


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

_DATE_RANGE_RE = re.compile(
    r"\b"
    r"(?:(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?"
    r"((?:19|20)\d{2})"
    r"\s*(?:-|–|—|to)\s*"
    r"(?:(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?"
    r"(Present|Current|Now|(?:19|20)\d{2})"
    r"\b",
    re.I,
)

_YEAR_RANGE_RE = re.compile(
    r"\b(19|20)\d{2}\s*(?:-|–|—|to)\s*(19|20)\d{2}\b"
)

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _parse_education(lines: List[str]) -> List[dict]:
    if not lines:
        return []

    cleaned = [
        _strip_bullet(line).strip()
        for line in lines
        if _strip_bullet(line).strip()
    ]

    if not cleaned:
        return []

    # Remove standalone page numbers.
    cleaned = [
        line for line in cleaned
        if not re.fullmatch(r"\d{1,3}", line)
    ]

    full_text = " ".join(cleaned)

    # Extract the education date range from the complete section.
    dates = _extract_date_range(full_text)

    degree = ""
    institution = ""
    location = ""
    score = ""
    description_parts = []

    # ---------------------------------------------------------------
    # Score
    # ---------------------------------------------------------------
    for line in cleaned:
        score_match = re.search(
            r"\b(?:cgpa|gpa|percentage|percent|score|grade)"
            r"\s*[:\-]?\s*"
            r"([0-9]+(?:\.[0-9]+)?"
            r"(?:\s*%|\s*/\s*[0-9]+)?)",
            line,
            re.I,
        )

        if score_match:
            score = score_match.group(0).strip()
            break

    # ---------------------------------------------------------------
    # Degree
    # ---------------------------------------------------------------
    for line in cleaned:
        if _looks_like_degree(line):
            degree = _remove_date_text(line)
            break

    # If the degree line contains dates joined directly to the text,
    # remove the years explicitly.
    if degree:
        degree = re.sub(
            r"\b(?:19|20)\d{2}\b",
            "",
            degree,
        )
        degree = re.sub(r"\s+", " ", degree).strip(" -–—")

    # ---------------------------------------------------------------
    # Institution + location
    # ---------------------------------------------------------------
    for line in cleaned:
        if line == degree:
            continue

        if score and line == score:
            continue

        # A line such as:
        # ICFAI Foundation for Higher Education, Hyderabad
        # should become:
        # institution = ICFAI Foundation for Higher Education
        # location = Hyderabad
        if "," in line:
            parts = [part.strip() for part in line.split(",")]

            if len(parts) >= 2:
                possible_location = parts[-1]

                if _looks_like_location(
                    ", ".join(parts[-2:])
                ):
                    institution = ", ".join(parts[:-1]).strip()
                    location = possible_location
                    break

        # Otherwise use institution detection.
        if _looks_like_institution(line):
            institution = line
            break

    # ---------------------------------------------------------------
    # Description
    # ---------------------------------------------------------------
    for line in cleaned:
        if line == degree:
            continue

        if line == institution:
            continue

        if score and line == score:
            continue

        if _is_date_only(line):
            continue

        # Remove dates from the line before comparing it with
        # the already-cleaned degree.
        line_without_dates = _remove_date_text(line)

        if degree and line_without_dates == degree:
            continue

        # Don't duplicate the institution/location line.
        if institution and line.startswith(institution):
            continue

        description_parts.append(line)


    return [{
        "degree": degree,
        "institution": institution,
        "location": location,
        "startYear": dates["startYear"],
        "endYear": dates["endYear"],
        "score": score,
        "description": " ".join(description_parts).strip(),
    }]
    

def _looks_like_degree(line: str) -> bool:
    lower = line.lower()

    keywords = (
        "b.tech", "btech", "b.e", "be ", "bachelor",
        "m.tech", "mtech", "m.e", "me ", "master",
        "mba", "mca", "phd", "doctor", "associate",
        "diploma", "b.sc", "bsc", "m.sc", "msc",
        "b.com", "m.com", "bba", "llb", "llm",
    )

    return any(keyword in lower for keyword in keywords)


def _looks_like_institution(line: str) -> bool:
    lower = line.lower()

    keywords = (
        "university", "college", "institute", "school",
        "academy", "campus",
    )

    return any(keyword in lower for keyword in keywords)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

_SKILL_CATEGORIES = {
    "languages": {
        "python", "java", "javascript", "typescript", "c", "c++", "c#",
        "go", "golang", "rust", "php", "ruby", "kotlin", "swift",
        "r", "matlab", "dart", "scala", "perl", "sql", "html", "css",
    },
    "frameworks": {
        "flask", "django", "fastapi", "react", "react.js", "reactjs",
        "angular", "vue", "vue.js", "node.js", "nodejs", "express",
        "spring", "spring boot", "laravel", "next.js", "nextjs",
        "tailwind", "bootstrap", "tensorflow", "pytorch", "keras",
        "pandas", "numpy", "scikit-learn", "sklearn",
    },
    "databases": {
        "mysql", "postgresql", "postgres", "sqlite", "mongodb",
        "redis", "oracle", "sql server", "mariadb", "firebase",
        "dynamodb", "cassandra",
    },
    "tools": {
        "git", "github", "gitlab", "docker", "kubernetes", "aws",
        "azure", "gcp", "google cloud", "linux", "windows",
        "postman", "jira", "figma", "jenkins", "vercel", "netlify",
        "heroku", "vs code", "visual studio", "npm", "yarn",
    },
}


def _parse_skills(lines: List[str]) -> dict:
    result = {
        "languages": [],
        "frameworks": [],
        "databases": [],
        "tools": [],
        "others": [],
    }

    if not lines:
        return result

    seen = set()

    for line in lines:
        line = _strip_bullet(line).strip()

        if not line:
            continue

        # Handle:
        # Languages: Python
        # Frontend: HTML, CSS, JavaScript
        # Backend: Flask
        # Databases: MySQL
        # Tools & Platforms: Git, GitHub, PythonAnywhere
        if ":" in line:
            label, values = line.split(":", 1)

            label = label.strip().lower()
            values = values.strip()

            # Ignore unknown labels only if there is no useful skill content.
            candidates = _split_skills(values)

            for skill in candidates:
                _add_parsed_skill(result, seen, skill)

        else:
            candidates = _split_skills(line)

            for skill in candidates:
                _add_parsed_skill(result, seen, skill)

    return result


def _add_parsed_skill(result: dict, seen: set, skill: str) -> None:
    skill = skill.strip(" -•·")

    if not skill:
        return

    if len(skill) > 45 or len(skill.split()) > 6:
        return

    key = re.sub(r"\s+", " ", skill.lower().strip())

    if key in seen:
        return

    seen.add(key)

    category = _classify_skill(key)

    if category:
        result[category].append(skill)
    else:
        result["others"].append(skill)
        
        
def _classify_skill(skill: str) -> str | None:
    normalized = skill.lower().strip()

    for category, values in _SKILL_CATEGORIES.items():
        if normalized in values:
            return category

    return None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

def _parse_projects(lines: List[str]) -> List[dict]:
    """
    Safely import project sections from extracted resume text.

    Important rule:
    A non-bullet line is treated as a new project title only when there is
    strong evidence that it is actually a title. Wrapped PDF text that looks
    like normal sentence continuation stays attached to the previous bullet.

    This intentionally favors a partial import over inventing extra projects.
    """
    if not lines:
        return []

    results = []
    current = None

    bullet_prefixes = ("•", "-", "–", "—", "▪", "◦", "‣", "⁃")

    def is_bullet(value: str) -> bool:
        return value.startswith(bullet_prefixes)

    def save_current():
        nonlocal current

        if not current:
            return

        current["technologies"] = _unique_nonempty(
            current["technologies"]
        )
        current["bullets"] = _unique_nonempty(
            current["bullets"]
        )

        # Do not create empty/noisy project entries.
        if (
            current["title"]
            and (
                current["bullets"]
                or current["technologies"]
                or current["github"]
                or current["liveDemo"]
            )
        ):
            results.append(current)

    def new_project(title: str):
        return {
            "title": title.strip(),
            "technologies": [],
            "bullets": [],
            "github": "",
            "liveDemo": "",
            "expanded": True,
        }

    def looks_like_project_title(value: str, next_line: str = "") -> bool:
        value = _strip_bullet(value).strip()

        if not value:
            return False

        if len(value) > 90 or len(value.split()) > 12:
            return False

        if _is_project_metadata_line(value):
            return False

        if _is_project_technology_line(value):
            return False

        if _contains_date_range(value):
            return False

        # A sentence continuation is much more likely to be normal content
        # than a project title.
        if value.endswith((".", ",", ";", ":", "?", "!")):
            return False

        words = value.split()

        # Lowercase sentence fragments such as:
        # "provides improvement recommendations."
        # "for enhancing skills..."
        # should stay with the previous bullet.
        first_alpha = next(
            (char for char in value if char.isalpha()),
            "",
        )
        if first_alpha and first_alpha.islower():
            return False

        # Project titles are usually title-cased, all-caps, or short names.
        title_case_like = (
            value == value.title()
            or value.isupper()
            or any(char.isupper() for char in value[1:])
        )

        if not title_case_like:
            return False

        # If the following line is clearly a tech stack or bullet, that is
        # strong evidence that this line is a project title.
        if next_line:
            if is_bullet(next_line):
                return True
            if _is_project_technology_line(next_line):
                return True

        # Conservative fallback for short title-like names.
        return len(words) <= 6

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()

        if not line:
            continue

        next_line = ""
        for candidate in lines[index + 1:]:
            candidate = candidate.strip()
            if candidate:
                next_line = candidate
                break

        # ---------------------------------------------------------------
        # Explicit project title
        # ---------------------------------------------------------------
        if (
            not is_bullet(line)
            and not _is_project_technology_line(line)
            and not _is_project_metadata_line(line)
            and looks_like_project_title(line, next_line)
        ):
            if current is not None:
                save_current()

            current = new_project(line)
            continue

        if current is None:
            # Do not invent a project from text that appears before a clear
            # project title.
            continue

        lower = line.lower()

        # ---------------------------------------------------------------
        # GitHub URL
        # ---------------------------------------------------------------
        if "github.com" in lower:
            match = _GITHUB_RE.search(line)

            if match:
                current["github"] = _clean_url(match.group(0))
                continue

        # ---------------------------------------------------------------
        # Live demo / deployment URL
        # ---------------------------------------------------------------
        if (
            "live demo" in lower
            or "demo" in lower
            or "deployed" in lower
            or "vercel.app" in lower
            or "netlify.app" in lower
            or "render.com" in lower
        ):
            urls = re.findall(
                r"(?:https?://|www\.)[^\s|]+",
                line,
                re.I,
            )

            if urls:
                current["liveDemo"] = _clean_url(urls[0])
                continue

        # ---------------------------------------------------------------
        # Explicit technology label
        # ---------------------------------------------------------------
        tech_match = re.match(
            r"^(?:technologies?|tech stack|stack)\s*[:\-]\s*(.+)$",
            line,
            re.I,
        )

        if tech_match:
            current["technologies"].extend(
                _split_skills(tech_match.group(1))
            )
            continue

        # ---------------------------------------------------------------
        # Technology-only line
        # ---------------------------------------------------------------
        if _is_project_technology_line(line):
            current["technologies"].extend(
                _split_skills(line)
            )
            continue

        # ---------------------------------------------------------------
        # Bullet
        # ---------------------------------------------------------------
        if is_bullet(line):
            bullet = _strip_bullet(line)

            if bullet:
                current["bullets"].append(bullet)

            continue

        # ---------------------------------------------------------------
        # Wrapped bullet continuation
        # ---------------------------------------------------------------
        # PDF extraction often turns:
        #
        #   • Built a resume optimizer that analyzes
        #     job requirements and provides recommendations.
        #
        # into two separate lines. The second line has no bullet marker.
        # Attach it to the previous bullet instead of making a fake project.
        if current["bullets"]:
            current["bullets"][-1] = (
                f"{current['bullets'][-1]} {line}".strip()
            )
        else:
            # If there is no bullet yet, retain the text as a bullet rather
            # than creating another project title.
            current["bullets"].append(line)

    save_current()

    return results


def _is_project_technology_line(line: str) -> bool:
    value = _strip_bullet(line).strip()

    if not value:
        return False

    # Explicit technology labels.
    if re.match(
        r"^(technologies?|tech stack|stack)\s*:",
        value,
        re.I,
    ):
        return True

    # Typical comma-separated technology line:
    # Python, Flask, MySQL
    parts = _split_skills(value)

    if len(parts) < 2:
        return False

    known = 0

    for part in parts:
        if _classify_skill(part.lower().strip()):
            known += 1

    return known >= 2


def _is_project_metadata_line(line: str) -> bool:
    lower = line.lower()

    return (
        "github.com" in lower
        or "live demo" in lower
        or "vercel.app" in lower
        or "netlify.app" in lower
        or "render.com" in lower
    )


def _looks_like_project_bullet(line: str) -> bool:
    return line.startswith(("•", "-", "–", "—"))

# ---------------------------------------------------------------------------
# Experience
# ---------------------------------------------------------------------------

def _parse_experience(lines: List[str]) -> List[dict]:
    if not lines:
        return []

    results = []

    job_title = ""
    company = ""
    location = ""
    responsibilities = []

    date_text = ""

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # Responsibilities
        if stripped.startswith(("•", "-", "–", "—")):
            responsibilities.append(
                _strip_bullet(stripped)
            )
            continue

        # Date-containing line
        if _contains_date_range(stripped):
            date_text = stripped

            # Remove date from line and keep whatever remains.
            without_date = _remove_date_text(stripped)

            if without_date:
                job_title = without_date

            continue

        # Location
        if _looks_like_location(stripped):
            location = stripped
            continue

        # First normal line = job title.
        if not job_title:
            job_title = stripped
            continue

        # Second normal line = company.
        if not company:
            company = stripped
            continue

    # Skip empty / placeholder experience.
    if not job_title and not responsibilities:
        return []

    if re.search(
        r"\b(no|none|n/?a)\s+(professional\s+)?experience\b",
        job_title,
        re.I,
    ):
        return []

    dates = _extract_date_range(date_text)

    results.append({
        "jobTitle": job_title,
        "company": company,
        "location": location,
        "startMonth": dates["startMonth"],
        "startYear": dates["startYear"],
        "endMonth": dates["endMonth"],
        "endYear": dates["endYear"],
        "currentlyWorking": dates["currentlyWorking"],
        "responsibilities": _unique_nonempty(
            responsibilities
        ),
        "expanded": True,
    })

    return results

# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------

def _parse_certifications(lines: List[str]) -> List[dict]:
    if not lines:
        return []

    results = []

    for raw_line in lines:
        line = _strip_bullet(raw_line).strip()

        if not line:
            continue

        # Ignore page numbers.
        if re.fullmatch(r"\d{1,3}", line):
            continue

        name = line
        organization = ""

        # Common format:
        # Python Basic — HackerRank
        # Intro to Programming - Kaggle
        match = re.split(r"\s+[—–-]\s+", line, maxsplit=1)

        if len(match) == 2:
            name = match[0].strip()
            organization = match[1].strip()

        month, year = _extract_month_year(line)

        results.append({
            "name": name,
            "organization": organization,
            "month": month,
            "year": year,
            "credentialId": "",
            "credentialUrl": "",
            "expanded": True,
        })

    return results

# ---------------------------------------------------------------------------
# Additional / custom sections
# ---------------------------------------------------------------------------

def _parse_additional_sections(
    sections: Dict[str, List[str]],
    known: set[str],
) -> List[dict]:
    results = []

    for key, values in sections.items():
        if not key.startswith("custom:"):
            continue

        title = key[len("custom:"):].strip().title()
        content = "\n".join(values).strip()

        if not title or not content:
            continue

        results.append({
            "id": f"imported-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}",
            "type": "text",
            "title": title,
            "content": content,
            "visible": True,
        })

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _group_entries(lines: List[str]) -> List[List[str]]:
    """
    Group lines into likely resume entries.

    Blank lines have already been removed, so grouping relies on bullets,
    date lines, and repeated structural patterns. This intentionally stays
    conservative: it is better to produce an editable partial entry than
    to merge unrelated content.
    """
    if not lines:
        return []

    entries = []
    current = []

    for line in lines:
        # A bullet belongs to the current entry.
        if line.startswith(("•", "-", "–", "—")):
            current.append(line)
            continue

        # If a new date-containing line appears after content, it generally
        # belongs to the current entry rather than starting a new one.
        current.append(line)

        # A date range followed by more content often ends an entry. We don't
        # immediately split because bullets can follow it.
        if _contains_date_range(line):
            continue

        # If the current entry has several lines and the next line looks like
        # a new title, split on the next iteration through a light heuristic.
        if len(current) >= 4 and _looks_like_entry_title(line):
            entries.append(current[:-1])
            current = [line]

    if current:
        entries.append(current)

    # If grouping produced one giant entry, try a safer second pass based on
    # date lines.
    if len(entries) == 1 and _count_date_ranges(lines) > 1:
        return _split_by_date_ranges(lines)

    return entries


def _looks_like_entry_title(line: str) -> bool:
    if len(line) > 80:
        return False

    if line.startswith(("•", "-", "–", "—")):
        return False

    if _contains_date_range(line):
        return False

    return len(line.split()) <= 8


def _split_by_date_ranges(lines: List[str]) -> List[List[str]]:
    groups = []
    current = []

    for line in lines:
        if current and _contains_date_range(line):
            current.append(line)
            groups.append(current)
            current = []
        else:
            current.append(line)

    if current:
        groups.append(current)

    return groups


def _contains_date_range(text: str) -> bool:
    return bool(_DATE_RANGE_RE.search(text))


def _count_date_ranges(lines: List[str]) -> int:
    return sum(1 for line in lines if _contains_date_range(line))


def _extract_date_range(text):
    value = text or ""

    match = _DATE_RANGE_RE.search(value)

    if match:
        start_month = (match.group(1) or "").title()
        start_year = match.group(2) or ""
        end_month = (match.group(3) or "").title()
        end_raw = match.group(4) or ""

        currently_working = end_raw.lower() in {
            "present",
            "current",
            "now",
        }

        end_year = "" if currently_working else end_raw

        return {
            "startMonth": start_month,
            "startYear": start_year,
            "endMonth": end_month,
            "endYear": end_year,
            "currentlyWorking": currently_working,
        }

    # Fallback for simple year ranges such as:
    # 2021 - 2025
    # 2021 – 2025
    # 2021 to 2025
    year_match = re.search(
        r"\b((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2})\b",
        value,
        re.I,
    )

    if year_match:
        return {
            "startMonth": "",
            "startYear": year_match.group(1),
            "endMonth": "",
            "endYear": year_match.group(2),
            "currentlyWorking": False,
        }

    return {
        "startMonth": "",
        "startYear": "",
        "endMonth": "",
        "endYear": "",
        "currentlyWorking": False,
    }

def _extract_month_year(text: str) -> Tuple[str, str]:
    month_pattern = (
        r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    )

    match = re.search(
        rf"\b{month_pattern}\s+((?:19|20)\d{{2}})\b",
        text,
        re.I,
    )

    if match:
        return _normalize_month(match.group(1)), match.group(2)

    year = re.search(r"\b((?:19|20)\d{2})\b", text)
    if year:
        return "", year.group(1)

    return "", ""


def _normalize_month(value: str) -> str:
    if not value:
        return ""

    key = value.lower()[:3]

    months = {
        "jan": "Jan",
        "feb": "Feb",
        "mar": "Mar",
        "apr": "Apr",
        "may": "May",
        "jun": "Jun",
        "jul": "Jul",
        "aug": "Aug",
        "sep": "Sep",
        "oct": "Oct",
        "nov": "Nov",
        "dec": "Dec",
    }

    return months.get(key, value)


def _is_date_only(line: str) -> bool:
    value = line.strip()

    if _DATE_RANGE_RE.fullmatch(value):
        return True

    if re.fullmatch(
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)?\s*"
        r"(?:19|20)\d{2}",
        value,
        re.I,
    ):
        return True

    return False


def _remove_date_text(text):
    value = text or ""

    value = _DATE_RANGE_RE.sub("", value)

    value = re.sub(
        r"\b(?:19|20)\d{2}\b",
        "",
        value,
    )

    value = re.sub(r"\s+", " ", value)

    return value.strip(" -–—,")


def _strip_bullet(line: str) -> str:
    return re.sub(r"^[•\-–—▪◦‣⁃]\s*", "", line).strip()


def _split_skills(value: str) -> List[str]:
    parts = re.split(r"\s*[,;|•·]\s*", value)
    return [
        item.strip()
        for item in parts
        if item.strip()
    ]


def _unique_nonempty(values: List[str]) -> List[str]:
    result = []
    seen = set()

    for value in values:
        value = value.strip()
        if not value:
            continue

        key = value.lower()
        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def _after_separator(line: str) -> str:
    if ":" in line:
        return line.split(":", 1)[1].strip()
    if "-" in line:
        return line.split("-", 1)[1].strip()
    return line.strip()


def _extract_years(text: str) -> List[str]:
    return re.findall(r"\b(?:19|20)\d{2}\b", text)


def _normalize_for_matching(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _parse_custom_content(values: List[str]) -> str:
    return "\n".join(values).strip()


__all__ = ["parse_resume"]
