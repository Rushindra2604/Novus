from __future__ import annotations

import json
from typing import Any

from .gemini_client import GeminiClient


SYSTEM_INSTRUCTION = """
You are the AI analysis engine for Novus ATS.

Your job is to interpret deterministic ATS analysis results and provide
useful, evidence-based feedback to the resume owner.

IMPORTANT RULES:

1. Never calculate, modify, or invent the ATS score.
2. Treat the provided ATS score and component scores as authoritative.
3. Never invent skills, experience, projects, certifications, achievements,
   education, or technologies that are not present in the supplied data.
4. Distinguish between:
   - something genuinely missing from the resume
   - something that may simply be expressed differently
5. Do not recommend adding a skill unless there is evidence that the user
   actually has that skill.
6. Give practical recommendations that the user can act on.
7. Prioritize required skills and critical gaps over minor improvements.
8. Keep the analysis concise, professional, and specific to the job.
9. Do not rewrite resume content in this step. Rewriting is handled by
   the separate AI rewriter.
10. Return valid JSON only.
"""


class ATSAIAnalyzer:
    """Gemini-powered interpretation layer for Novus ATS results."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    def analyze(
        self,
        *,
        resume: dict[str, Any],
        job_description: dict[str, Any],
        score: dict[str, Any],
        matches: dict[str, Any],
        gaps: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze deterministic ATS results using Gemini."""

        payload = self._build_payload(
            resume=resume,
            job_description=job_description,
            score=score,
            matches=matches,
            gaps=gaps,
        )

        prompt = self._build_prompt(payload)

        response = self.client.generate(
            prompt,
            system_instruction=SYSTEM_INSTRUCTION,
        )

        return self._parse_response(response)

    @staticmethod
    def _build_payload(
        *,
        resume: dict[str, Any],
        job_description: dict[str, Any],
        score: dict[str, Any],
        matches: dict[str, Any],
        gaps: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the structured information sent to Gemini."""

        return {
            "resume": {
                "title": resume.get("title", ""),
                "summary": resume.get("summary", ""),
                "skills": resume.get("skills", {}),
                "experience": resume.get("experience", []),
                "projects": resume.get("projects", []),
                "education": resume.get("education", []),
                "certifications": resume.get("certifications", []),
            },
            "job_description": {
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
                "experience_requirements": job_description.get(
                    "experience_requirements", []
                ),
                "education_requirements": job_description.get(
                    "education_requirements", []
                ),
                "responsibilities": job_description.get(
                    "responsibilities", []
                ),
            },
            "score": score,
            "matches": matches,
            "gaps": gaps,
        }

    @staticmethod
    def _build_prompt(payload: dict[str, Any]) -> str:
        """Create the Gemini analysis prompt."""

        return f"""
Analyze the following Novus ATS results.

The numerical score, matching results, and identified gaps were produced
by deterministic software. Do not recalculate them.

Return JSON using exactly this structure:

{{
  "overall_assessment": "string",
  "strengths": [
    "string"
  ],
  "critical_issues": [
    "string"
  ],
  "improvement_priorities": [
    {{
      "priority": 1,
      "area": "string",
      "issue": "string",
      "recommendation": "string"
    }}
  ]
}}

Requirements for the response:

- overall_assessment: 2-4 sentences explaining the candidate's overall
  position for this job.
- strengths: 3-5 specific strengths supported by the supplied resume and
  matching data.
- critical_issues: focus on important gaps that materially affect the
  application. Do not invent missing requirements.
- improvement_priorities: order the most useful improvements first.
- Recommendations must be based only on evidence in the supplied data.
- If a required skill is missing, do not tell the user to falsely add it.
  Instead explain that they should only add it if they genuinely have
  the skill, otherwise focus on demonstrated transferable experience.
- Do not include markdown.
- Return JSON only.

DATA:

{json.dumps(payload, indent=2, ensure_ascii=False)}
"""

    @staticmethod
    def _parse_response(response: str) -> dict[str, Any]:
        """Parse and validate Gemini's JSON response."""

        try:
            result = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini analysis must be a JSON object."
            )

        required_fields = {
            "overall_assessment",
            "strengths",
            "critical_issues",
            "improvement_priorities",
        }

        missing_fields = required_fields - result.keys()

        if missing_fields:
            raise ValueError(
                "Gemini analysis is missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        if not isinstance(result["overall_assessment"], str):
            raise ValueError(
                "overall_assessment must be a string."
            )

        for field in ("strengths", "critical_issues"):
            if not isinstance(result[field], list):
                raise ValueError(
                    f"{field} must be a list."
                )

        if not isinstance(result["improvement_priorities"], list):
            raise ValueError(
                "improvement_priorities must be a list."
            )

        return result