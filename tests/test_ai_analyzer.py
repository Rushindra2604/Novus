from ats.ai.analyzer import ATSAIAnalyzer


class FakeGeminiClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt = None
        self.last_system_instruction = None

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
    ) -> str:
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction
        return self.response


def sample_resume():
    return {
        "title": "Backend Developer",
        "summary": "Python developer with Flask experience.",
        "skills": {
            "languages": ["Python"],
            "frameworks": ["Flask"],
            "databases": ["PostgreSQL"],
            "tools": ["Git"],
        },
        "experience": [],
        "projects": [
            {
                "name": "API Project",
                "description": "Built a Flask REST API.",
            }
        ],
        "education": [],
        "certifications": [],
    }


def sample_job_description():
    return {
        "title": "Backend Developer",
        "summary": "Backend development role.",
        "required_skills": ["Python", "Flask", "Docker"],
        "preferred_skills": ["AWS"],
        "technical_keywords": ["REST API", "PostgreSQL"],
        "experience_requirements": [],
        "education_requirements": [],
        "responsibilities": [
            "Build backend APIs",
            "Maintain backend services",
        ],
    }


def sample_score():
    return {
        "overall_score": 68,
        "level": "Moderate",
        "components": {
            "required_skills": 66,
            "technical_keywords": 100,
            "practical_experience": 80,
            "responsibilities": 50,
            "parseability": 100,
            "education": None,
            "preferred_skills": 0,
        },
    }


def sample_matches():
    return {
        "required_skills": {
            "matched": ["Python", "Flask"],
            "missing": ["Docker"],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["AWS"],
        },
        "technical_keywords": {
            "matched": ["REST API", "PostgreSQL"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build backend APIs"],
            "missing": ["Maintain backend services"],
        },
    }


def sample_gaps():
    return {
        "gaps": [
            {
                "category": "required_skills",
                "item": "Docker",
                "priority": "critical",
            },
            {
                "category": "preferred_skills",
                "item": "AWS",
                "priority": "medium",
            },
        ]
    }


def valid_ai_response():
    return """
{
    "overall_assessment": "The resume shows strong Python and Flask alignment but has an important gap in Docker.",
    "strengths": [
        "Strong Python and Flask alignment",
        "Relevant REST API experience",
        "PostgreSQL experience matches the role"
    ],
    "critical_issues": [
        "Docker is listed as a required skill but is not demonstrated in the resume."
    ],
    "improvement_priorities": [
        {
            "priority": 1,
            "area": "Required skills",
            "issue": "Docker is missing",
            "recommendation": "Only add Docker if you genuinely have experience with it."
        }
    ]
}
"""


def test_analyzer_returns_structured_result():
    client = FakeGeminiClient(valid_ai_response())
    analyzer = ATSAIAnalyzer(client)

    result = analyzer.analyze(
        resume=sample_resume(),
        job_description=sample_job_description(),
        score=sample_score(),
        matches=sample_matches(),
        gaps=sample_gaps(),
    )

    assert isinstance(result, dict)
    assert "overall_assessment" in result
    assert "strengths" in result
    assert "critical_issues" in result
    assert "improvement_priorities" in result


def test_analyzer_passes_context_to_gemini():
    client = FakeGeminiClient(valid_ai_response())
    analyzer = ATSAIAnalyzer(client)

    analyzer.analyze(
        resume=sample_resume(),
        job_description=sample_job_description(),
        score=sample_score(),
        matches=sample_matches(),
        gaps=sample_gaps(),
    )

    assert "Backend Developer" in client.last_prompt
    assert "Docker" in client.last_prompt
    assert "68" in client.last_prompt


def test_analyzer_uses_system_instruction():
    client = FakeGeminiClient(valid_ai_response())
    analyzer = ATSAIAnalyzer(client)

    analyzer.analyze(
        resume=sample_resume(),
        job_description=sample_job_description(),
        score=sample_score(),
        matches=sample_matches(),
        gaps=sample_gaps(),
    )

    assert client.last_system_instruction is not None
    assert "Never calculate" in client.last_system_instruction


def test_analyzer_rejects_invalid_json():
    client = FakeGeminiClient("not valid json")
    analyzer = ATSAIAnalyzer(client)

    try:
        analyzer.analyze(
            resume=sample_resume(),
            job_description=sample_job_description(),
            score=sample_score(),
            matches=sample_matches(),
            gaps=sample_gaps(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "invalid JSON" in str(exc)


def test_analyzer_rejects_missing_fields():
    client = FakeGeminiClient(
        '{"overall_assessment": "Good match."}'
    )
    analyzer = ATSAIAnalyzer(client)

    try:
        analyzer.analyze(
            resume=sample_resume(),
            job_description=sample_job_description(),
            score=sample_score(),
            matches=sample_matches(),
            gaps=sample_gaps(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "missing required fields" in str(exc)