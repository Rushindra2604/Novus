from __future__ import annotations

import json
from typing import Any

from .gemini_client import GeminiClient


SYSTEM_INSTRUCTION = """
You are the AI resume rewriting engine for Novus ATS.

Your job is to improve the wording of EXISTING resume content for
a specific job description while preserving the candidate's actual
experience exactly.

The candidate's original content and supplied resume context are the
ONLY sources of truth about what the candidate has done.

============================================================
STRICT EVIDENCE-PRESERVATION RULES
============================================================

1. NEVER invent or add:
   - skills
   - technologies
   - frameworks
   - libraries
   - tools
   - platforms
   - databases
   - employers
   - projects
   - responsibilities
   - achievements
   - leadership
   - ownership
   - metrics
   - percentages
   - user counts
   - performance improvements
   - business results
   - certifications
   - education
   - years of experience

2. NEVER infer a responsibility that is not explicitly supported.

   For example:

   "Implemented a notes management system"

   MUST NOT become:

   "Architected and led development of a notes management platform"

   because "architected" and "led" imply responsibilities that may not
   have been performed by the candidate.

3. NEVER upgrade the candidate's level of ownership.

   Do not transform:

   - used → designed
   - implemented → architected
   - assisted → led
   - contributed → owned
   - worked on → managed
   - developed → led development

   unless the original resume explicitly supports that stronger claim.

4. NEVER create an outcome that was not stated.

   Do not add claims such as:

   - improved performance
   - reduced processing time
   - increased efficiency
   - improved scalability
   - enhanced conversion
   - increased accuracy
   - served users
   - reduced costs

   unless the original resume explicitly contains that result.

5. NEVER create a metric.

   If the original says:

   "Implemented CRUD functionality"

   do NOT produce:

   "Implemented CRUD functionality for 1,000+ users."

6. NEVER add a technology merely because it appears in the
   job description.

   If the JD requires AWS but the resume does not demonstrate AWS,
   do not insert AWS into the rewrite.

7. NEVER convert a general concept into a specific technology claim.

   For example:

   "worked with databases"

   must not become:

   "developed PostgreSQL database systems"

   unless PostgreSQL is explicitly supported by the resume context.

8. You MAY improve:
   - grammar
   - sentence structure
   - clarity
   - conciseness
   - action-oriented phrasing
   - readability
   - terminology already supported by the resume
   - relevance to the supplied job description

9. You MAY use a technology or keyword from the supplied resume
   context when it genuinely describes the original content.

10. You MAY change word forms.

    Examples:

    implement → implemented
    extract → extraction
    process → processing
    automate → automated

    These are wording changes, not new facts.

11. Generic descriptive wording is allowed when it does not introduce
    a new factual claim.

    Examples:

    - workflow
    - process
    - functionality
    - technical
    - development
    - application
    - system

12. Be conservative.

    When uncertain whether a stronger statement is supported,
    KEEP THE ORIGINAL MEANING instead of making the claim stronger.

13. The rewritten content must remain factually equivalent to the
    original content.

14. Do not optimize for sounding impressive at the expense of factual
    accuracy.

============================================================
JOB DESCRIPTION USAGE
============================================================

Use the job description only to understand:

- which supported skills are relevant
- which supported terminology is useful
- which aspects of the existing experience should be emphasized

The JD is NOT permission to add missing experience.

For example:

Resume:
"Built Flask web applications."

JD:
"Experience with Flask, Docker and AWS."

Valid:
"Developed Flask web applications."

Invalid:
"Developed and deployed Flask applications using Docker and AWS."

============================================================
REWRITE QUALITY
============================================================

The result should sound like a stronger version of the candidate's
ORIGINAL statement, not like a fictional replacement.

Prefer:

"Implemented PDF parsing using PDFPlumber to extract and process
resume data."

→

"Implemented automated resume data extraction and processing using
PDFPlumber for PDF parsing."

Do NOT prefer:

"Engineered a scalable PDF processing pipeline that improved
processing efficiency by 40%."

The second example introduces unsupported ownership, scalability,
and a metric.

============================================================
OUTPUT
============================================================

Return valid JSON only.

Never include markdown fences.

For bullet rewriting return:

{
  "original": "...",
  "rewritten": "...",
  "changes": [
    "..."
  ],
  "used_keywords": [
    "..."
  ],
  "warnings": [
    "..."
  ]
}

For summary rewriting return the same structure.

The "original" field must exactly match the supplied original content.

The "rewritten" field must contain only an evidence-preserving rewrite.

"used_keywords" must contain only relevant terminology actually
supported by the supplied resume content.

If a potentially useful JD keyword is missing from the candidate's
evidence, do NOT use it.

If the rewrite cannot be improved without changing the factual meaning,
return a conservative rewrite that stays close to the original.

============================================================
FINAL CHECK BEFORE RESPONDING
============================================================

Before returning the JSON, internally verify:

- Did I add a new technology?
- Did I add a new tool?
- Did I add a new responsibility?
- Did I increase the candidate's ownership?
- Did I add a result?
- Did I add a metric?
- Did I imply leadership?
- Did I imply deployment?
- Did I imply scale?
- Did I imply performance improvement?
- Did I add anything that the candidate did not actually state?

If YES to any of these, remove that claim.

The candidate's actual experience is more important than making the
sentence sound impressive.
"""


class ATSRewriter:
    """Gemini-powered resume content improvement engine."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    def rewrite_bullet(
        self,
        *,
        bullet: str,
        job_description: dict[str, Any],
        resume_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Rewrite one resume bullet using evidence from the resume."""

        if not isinstance(bullet, str) or not bullet.strip():
            raise ValueError("Bullet cannot be empty.")

        payload = {
            "original_bullet": bullet.strip(),
            "job_description": self._build_job_context(job_description),
            "resume_context": resume_context or {},
        }

        prompt = self._build_bullet_prompt(payload)

        response = self.client.generate(
            prompt,
            system_instruction=SYSTEM_INSTRUCTION,
        )

        return self._parse_response(response)

    def rewrite_summary(
        self,
        *,
        summary: str,
        job_description: dict[str, Any],
        resume_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Rewrite a resume summary using only existing evidence."""

        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Summary cannot be empty.")

        payload = {
            "original_summary": summary.strip(),
            "job_description": self._build_job_context(job_description),
            "resume_context": resume_context or {},
        }

        prompt = self._build_summary_prompt(payload)

        response = self.client.generate(
            prompt,
            system_instruction=SYSTEM_INSTRUCTION,
        )

        return self._parse_response(response)

    @staticmethod
    def _build_job_context(
        job_description: dict[str, Any],
    ) -> dict[str, Any]:
        """Keep only useful JD information for rewriting."""

        return {
            "title": job_description.get("title", ""),
            "summary": job_description.get("summary", ""),
            "required_skills": job_description.get(
                "required_skills", []
            ),
            "preferred_skills": job_description.get(
                "preferred_skills", []
            ),
            "technical_keywords": job_description.get(
                "technical_keywords", []
            ),
            "responsibilities": job_description.get(
                "responsibilities", []
            ),
        }

    @staticmethod
    def _build_bullet_prompt(
        payload: dict[str, Any],
    ) -> str:
        """Create the prompt used for bullet rewriting."""

        return f"""
Rewrite the following resume bullet for the target job.

The rewritten bullet must:

- preserve the original factual meaning
- use stronger action-oriented language where appropriate
- emphasize relevant responsibilities already demonstrated
- naturally use relevant job-description terminology only when supported
  by the original bullet or resume context
- remain concise
- never introduce unsupported skills or achievements

Return JSON using exactly:

{{
  "original": "original bullet",
  "rewritten": "improved bullet",
  "changes": [
    "brief explanation of a change"
  ],
  "used_keywords": [
    "keywords actually supported by the original content"
  ],
  "warnings": [
    "any important limitation or unsupported job requirement"
  ]
}}

If no meaningful improvement is possible, return the original bullet
as the rewritten value.

Do not use markdown.
Return JSON only.

DATA:

{json.dumps(payload, indent=2, ensure_ascii=False)}
"""

    @staticmethod
    def _build_summary_prompt(
        payload: dict[str, Any],
    ) -> str:
        """Create the prompt used for summary rewriting."""

        return f"""
Rewrite the following resume summary for the target job.

The rewritten summary must:

- preserve the candidate's actual background
- emphasize relevant skills already demonstrated
- use relevant terminology from the job description only when supported
- remain concise and professional
- never invent experience, technologies, achievements, metrics, or
  qualifications

Return JSON using exactly:

{{
  "original": "original summary",
  "rewritten": "improved summary",
  "changes": [
    "brief explanation of a change"
  ],
  "used_keywords": [
    "keywords actually supported by the resume"
  ],
  "warnings": [
    "any important limitation or unsupported job requirement"
  ]
}}

Do not use markdown.
Return JSON only.

DATA:

{json.dumps(payload, indent=2, ensure_ascii=False)}
"""

    @staticmethod
    def _parse_response(response: str) -> dict[str, Any]:
        """Parse and validate the AI response."""

        try:
            result = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini rewrite must be a JSON object."
            )

        required_fields = {
            "original",
            "rewritten",
            "changes",
            "used_keywords",
            "warnings",
        }

        missing_fields = required_fields - result.keys()

        if missing_fields:
            raise ValueError(
                "Gemini rewrite is missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        if not isinstance(result["original"], str):
            raise ValueError("original must be a string.")

        if not isinstance(result["rewritten"], str):
            raise ValueError("rewritten must be a string.")

        for field in (
            "changes",
            "used_keywords",
            "warnings",
        ):
            if not isinstance(result[field], list):
                raise ValueError(f"{field} must be a list.")

        return result