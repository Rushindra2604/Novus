from ats.ai.rewriter import ATSRewriter


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


def sample_job_description():
    return {
        "title": "Backend Developer",
        "summary": "Backend development role.",
        "required_skills": [
            "Python",
            "Flask",
            "Docker",
        ],
        "preferred_skills": [
            "AWS",
        ],
        "technical_keywords": [
            "REST API",
            "PostgreSQL",
        ],
        "responsibilities": [
            "Build backend APIs",
            "Maintain backend services",
        ],
    }


def sample_resume_context():
    return {
        "skills": {
            "languages": ["Python"],
            "frameworks": ["Flask"],
            "databases": ["PostgreSQL"],
        },
        "projects": [
            {
                "name": "API Project",
                "description": "Built a Flask REST API."
            }
        ],
    }


def valid_bullet_response():
    return """
{
    "original": "Developed a Flask API for a college project.",
    "rewritten": "Developed a Flask REST API for a college project, implementing backend API endpoints.",
    "changes": [
        "Made the API responsibility more explicit.",
        "Used REST API terminology supported by the original content."
    ],
    "used_keywords": [
        "Flask",
        "REST API"
    ],
    "warnings": []
}
"""


def valid_summary_response():
    return """
{
    "original": "Python developer with Flask experience.",
    "rewritten": "Python developer with Flask experience focused on building REST APIs.",
    "changes": [
        "Emphasized the candidate's demonstrated API experience."
    ],
    "used_keywords": [
        "Python",
        "Flask",
        "REST APIs"
    ],
    "warnings": []
}
"""


def test_rewrite_bullet_returns_structured_result():
    client = FakeGeminiClient(valid_bullet_response())
    rewriter = ATSRewriter(client)

    result = rewriter.rewrite_bullet(
        bullet="Developed a Flask API for a college project.",
        job_description=sample_job_description(),
        resume_context=sample_resume_context(),
    )

    assert isinstance(result, dict)
    assert result["original"]
    assert result["rewritten"]
    assert isinstance(result["changes"], list)
    assert isinstance(result["used_keywords"], list)
    assert isinstance(result["warnings"], list)


def test_rewrite_bullet_passes_job_context():
    client = FakeGeminiClient(valid_bullet_response())
    rewriter = ATSRewriter(client)

    rewriter.rewrite_bullet(
        bullet="Developed a Flask API for a college project.",
        job_description=sample_job_description(),
        resume_context=sample_resume_context(),
    )

    assert "Docker" in client.last_prompt
    assert "REST API" in client.last_prompt
    assert "Flask" in client.last_prompt


def test_rewrite_bullet_passes_resume_context():
    client = FakeGeminiClient(valid_bullet_response())
    rewriter = ATSRewriter(client)

    rewriter.rewrite_bullet(
        bullet="Developed a Flask API for a college project.",
        job_description=sample_job_description(),
        resume_context=sample_resume_context(),
    )

    assert "PostgreSQL" in client.last_prompt
    assert "API Project" in client.last_prompt


def test_rewrite_summary_returns_structured_result():
    client = FakeGeminiClient(valid_summary_response())
    rewriter = ATSRewriter(client)

    result = rewriter.rewrite_summary(
        summary="Python developer with Flask experience.",
        job_description=sample_job_description(),
        resume_context=sample_resume_context(),
    )

    assert isinstance(result, dict)
    assert result["original"]
    assert result["rewritten"]


def test_rewriter_uses_safety_instruction():
    client = FakeGeminiClient(valid_bullet_response())
    rewriter = ATSRewriter(client)

    rewriter.rewrite_bullet(
        bullet="Developed a Flask API for a college project.",
        job_description=sample_job_description(),
        resume_context=sample_resume_context(),
    )

    assert client.last_system_instruction is not None
    assert "NEVER invent" in client.last_system_instruction


def test_rewriter_rejects_empty_bullet():
    client = FakeGeminiClient(valid_bullet_response())
    rewriter = ATSRewriter(client)

    try:
        rewriter.rewrite_bullet(
            bullet="",
            job_description=sample_job_description(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Bullet cannot be empty" in str(exc)


def test_rewriter_rejects_empty_summary():
    client = FakeGeminiClient(valid_summary_response())
    rewriter = ATSRewriter(client)

    try:
        rewriter.rewrite_summary(
            summary="",
            job_description=sample_job_description(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Summary cannot be empty" in str(exc)


def test_rewriter_rejects_invalid_json():
    client = FakeGeminiClient("not json")
    rewriter = ATSRewriter(client)

    try:
        rewriter.rewrite_bullet(
            bullet="Developed a Flask API.",
            job_description=sample_job_description(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "invalid JSON" in str(exc)


def test_rewriter_rejects_missing_fields():
    client = FakeGeminiClient(
        '{"original": "Developed a Flask API."}'
    )
    rewriter = ATSRewriter(client)

    try:
        rewriter.rewrite_bullet(
            bullet="Developed a Flask API.",
            job_description=sample_job_description(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "missing required fields" in str(exc)