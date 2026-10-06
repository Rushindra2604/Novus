from ats.pipeline import ATSAnalysisPipeline

class FakeAIAnalyzer:
    def analyze(
        self,
        *,
        resume,
        job_description,
        score,
        matches,
        gaps,
    ):
        return {
            "overall_assessment": "Good candidate alignment.",
            "strengths": [
                "Relevant Python experience."
            ],
            "critical_issues": [
                "Docker is missing."
            ],
            "improvement_priorities": [
                {
                    "priority": 1,
                    "area": "Skills",
                    "issue": "Docker is missing.",
                    "recommendation": (
                        "Only add Docker if the candidate "
                        "actually has that experience."
                    ),
                }
            ],
        }


class FakeAIRewriter:
    def rewrite_bullet(
        self,
        *,
        bullet,
        job_description,
        resume_context,
    ):
        return {
            "original": bullet,
            "rewritten": "Built a Flask REST API.",
            "changes": [
                "Improved clarity."
            ],
            "used_keywords": [
                "Flask",
                "REST API",
            ],
            "warnings": [],
        }

    def rewrite_summary(
        self,
        *,
        summary,
        job_description,
        resume_context,
    ):
        return {
            "original": summary,
            "rewritten": (
                "Python developer with Flask experience."
            ),
            "changes": [
                "Improved relevance."
            ],
            "used_keywords": [
                "Python",
                "Flask",
            ],
            "warnings": [],
        }


def fake_resume_parser(text, fallback_title="Untitled Resume"):
    return {
        "title": fallback_title,
        "personal": {},
        "summary": "Python developer with Flask experience.",
        "education": [],
        "skills": {
            "languages": ["Python"],
            "frameworks": ["Flask"],
            "databases": ["PostgreSQL"],
            "tools": [],
            "others": [],
        },
        "projects": [
            {
                "name": "API Project",
                "description": "Built a Flask REST API.",
            }
        ],
        "experience": [],
        "certifications": [],
        "additionalSections": [],
    }


def test_pipeline_returns_complete_structure():
    pipeline = ATSAnalysisPipeline(
        resume_parser=fake_resume_parser,
        ai_analyzer=FakeAIAnalyzer(),
        ai_rewriter=FakeAIRewriter(),
    )

    result = pipeline.analyze(
        resume_text="Python developer with Flask experience.",
        job_description_text="""
        Backend Developer

        Required Skills:
        Python
        Flask
        Docker

        Preferred Skills:
        AWS

        Responsibilities:
        Build backend APIs.
        """,
    )

    assert "resume" in result
    assert "job_description" in result
    assert "matches" in result
    assert "score" in result
    assert "gaps" in result
    assert "gap_summary" in result
    assert "ai_analysis" in result
    assert "ai_rewrites" in result
    
    assert "parseability" in result
    assert 0 <= result["parseability"]["score"] <= 100
    assert (
        result["score"]["component_scores"]["parseability"]
        is not None
    )


def test_pipeline_marks_ai_as_enabled():
    pipeline = ATSAnalysisPipeline(
        resume_parser=fake_resume_parser,
        ai_analyzer=FakeAIAnalyzer(),
        ai_rewriter=FakeAIRewriter(),
    )

    result = pipeline.analyze(
        resume_text="Python developer.",
        job_description_text="Python developer required.",
    )

    assert result["meta"]["ai_enabled"] is True
    assert result["meta"]["pipeline"] == "novus_ats_ai"


def test_pipeline_runs_ai_analysis():
    pipeline = ATSAnalysisPipeline(
        resume_parser=fake_resume_parser,
        ai_analyzer=FakeAIAnalyzer(),
        ai_rewriter=FakeAIRewriter(),
    )

    result = pipeline.analyze(
        resume_text="Python developer.",
        job_description_text="Python developer required.",
    )

    assert result["ai_analysis"]["overall_assessment"] == (
        "Good candidate alignment."
    )


def test_pipeline_can_rewrite_bullets():
    pipeline = ATSAnalysisPipeline(
        resume_parser=fake_resume_parser,
        ai_analyzer=FakeAIAnalyzer(),
        ai_rewriter=FakeAIRewriter(),
    )

    result = pipeline.analyze(
        resume_text="Python developer.",
        job_description_text="Python developer required.",
        rewrite_bullets=[
            "Developed a Flask API."
        ],
    )

    bullets = result["ai_rewrites"]["bullets"]

    assert len(bullets) == 1
    assert bullets[0]["rewritten"] == (
        "Built a Flask REST API."
    )
    assert "validation" in bullets[0]


def test_pipeline_can_rewrite_summary():
    pipeline = ATSAnalysisPipeline(
        resume_parser=fake_resume_parser,
        ai_analyzer=FakeAIAnalyzer(),
        ai_rewriter=FakeAIRewriter(),
    )

    result = pipeline.analyze(
        resume_text="Python developer.",
        job_description_text="Python developer required.",
        rewrite_summary=True,
    )

    summary = result["ai_rewrites"]["summary"]

    assert summary is not None
    assert summary["rewritten"] == (
        "Python developer with Flask experience."
    )
    assert "validation" in summary


def test_pipeline_does_not_rewrite_when_not_requested():
    pipeline = ATSAnalysisPipeline(
        resume_parser=fake_resume_parser,
        ai_analyzer=FakeAIAnalyzer(),
        ai_rewriter=FakeAIRewriter(),
    )

    result = pipeline.analyze(
        resume_text="Python developer.",
        job_description_text="Python developer required.",
    )

    assert result["ai_rewrites"]["bullets"] == []
    assert result["ai_rewrites"]["summary"] is None