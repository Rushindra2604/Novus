from __future__ import annotations

from typing import Any

from .gap_analyzer import (
    build_gap_analysis,
    build_gap_summary,
)
from .jd_parser import parse_job_description
from .keyword_matcher import build_match_analysis
from .resume_analyzer import build_resume_analysis
from .score_engine import calculate_ats_score
from .parseability_analyzer import analyze_parseability

from .ai.analyzer import ATSAIAnalyzer
from .ai.rewriter import ATSRewriter
from .ai.validator import validate_rewrite


class ATSAnalysisPipeline:
    """
    Orchestrates the complete Novus ATS analysis flow.

    Deterministic modules are the source of truth for:

    - resume parsing
    - job description parsing
    - matching
    - scoring
    - gap analysis

    Gemini is responsible for:

    - contextual analysis
    - improvement suggestions
    - resume rewriting

    AI output is validated before being returned.
    """

    def __init__(
        self,
        *,
        resume_parser: Any,
        ai_analyzer: ATSAIAnalyzer | None = None,
        ai_rewriter: ATSRewriter | None = None,
    ) -> None:
        self.resume_parser = resume_parser
        self.ai_analyzer = ai_analyzer or ATSAIAnalyzer()
        self.ai_rewriter = ai_rewriter or ATSRewriter()

    def analyze(
        self,
        *,
        resume_text: str,
        job_description_text: str,
        resume_title: str = "Untitled Resume",
        rewrite_bullets: list[str] | None = None,
        rewrite_summary: bool = False,
    ) -> dict[str, Any]:
        """
        Run the complete Novus ATS analysis pipeline.
        """

        # =========================================================
        # STEP 1 — Resume analysis
        # =========================================================

        resume = build_resume_analysis(
            resume_text,
            fallback_title=resume_title,
            parser=self.resume_parser,
        )

        # =========================================================
        # STEP 2 — Job description parsing
        # =========================================================

        job_description = parse_job_description(
            job_description_text
        )

        # =========================================================
        # STEP 3 — Resume/JD matching
        # =========================================================

        match_analysis = build_match_analysis(
            resume,
            job_description,
        )

        # =========================================================
        # STEP 4 — Deterministic ATS scoring
        # =========================================================

        parseability_analysis = analyze_parseability(
            resume_text,
            resume,
        )

        score = calculate_ats_score(
            match_analysis,
            resume_analysis=resume,
            parseability_analysis=parseability_analysis,
        )

        # Add human-readable score level.
        # Keep the numerical score produced by the deterministic
        # scoring engine unchanged.

        score["level"] = self._get_score_level(
            score.get("score", 0.0)
        )

        # =========================================================
        # STEP 5 — Gap analysis
        # =========================================================

        gap_analysis = build_gap_analysis(
            match_analysis
        )

        gap_summary = build_gap_summary(
            gap_analysis
        )

        # =========================================================
        # STEP 6 — Gemini contextual analysis
        # =========================================================

        ai_analysis = self.ai_analyzer.analyze(
            resume=resume,
            job_description=job_description,
            score=score,
            matches=match_analysis,
            gaps=gap_analysis,
        )

        # =========================================================
        # STEP 7 — Optional AI bullet rewriting
        # =========================================================

        bullet_rewrites: list[dict[str, Any]] = []

        for bullet in rewrite_bullets or []:
            rewrite = self.ai_rewriter.rewrite_bullet(
                bullet=bullet,
                job_description=job_description,
                resume_context=resume,
            )

            validation = validate_rewrite(
                original=rewrite["original"],
                rewritten=rewrite["rewritten"],
                resume_context=resume,
            )

            bullet_rewrites.append(
                {
                    **rewrite,
                    "validation": validation,
                }
            )

        # =========================================================
        # STEP 8 — Optional AI summary rewriting
        # =========================================================

        summary_rewrite = None

        if rewrite_summary and resume.get("summary"):
            summary_rewrite = (
                self.ai_rewriter.rewrite_summary(
                    summary=resume["summary"],
                    job_description=job_description,
                    resume_context=resume,
                )
            )

            summary_rewrite["validation"] = (
                validate_rewrite(
                    original=summary_rewrite["original"],
                    rewritten=summary_rewrite["rewritten"],
                    resume_context=resume,
                )
            )

        # =========================================================
        # STEP 9 — Final result
        # =========================================================

        return {
            "schema_version": "1.0",

            "resume": resume,

            "job_description": job_description,

            "matches": match_analysis,

            "score": score,
            
            "parseability": parseability_analysis,

            "gaps": gap_analysis,

            "gap_summary": gap_summary,

            "ai_analysis": ai_analysis,

            "ai_rewrites": {
                "bullets": bullet_rewrites,
                "summary": summary_rewrite,
            },

            "meta": {
                "ai_enabled": True,
                "pipeline": "novus_ats_ai",
            },
        }

    @staticmethod
    def _get_score_level(score: float) -> str:
        """
        Convert the deterministic ATS score into a level.
        """

        if score >= 85:
            return "Excellent"

        if score >= 70:
            return "Strong"

        if score >= 55:
            return "Moderate"

        if score >= 40:
            return "Needs Improvement"

        return "Weak"