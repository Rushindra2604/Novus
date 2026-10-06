from ats.ai.validator import (
    find_new_numeric_claims,
    find_unsupported_keywords,
    validate_rewrite,
)


def sample_resume_context():
    return {
        "summary": "Python developer with Flask experience.",
        "skills": {
            "languages": ["Python"],
            "frameworks": ["Flask"],
            "databases": ["PostgreSQL"],
        },
        "projects": [
            {
                "name": "API Project",
                "description": "Built a Flask REST API using PostgreSQL.",
            }
        ],
    }


def test_safe_rewrite():
    result = validate_rewrite(
        original="Built a Flask REST API.",
        rewritten="Built a Flask REST API.",
        resume_context=sample_resume_context(),
    )

    assert result["is_safe"] is True
    assert result["warnings"] == []


def test_detects_unsupported_keyword():
    result = validate_rewrite(
        original="Built a Flask REST API.",
        rewritten="Built a Flask REST API using Docker.",
        resume_context=sample_resume_context(),
    )

    assert result["is_safe"] is False
    assert "docker" in result["unsupported_keywords"]


def test_resume_context_can_support_keyword():
    result = validate_rewrite(
        original="Built a Flask API.",
        rewritten="Built a Flask REST API using PostgreSQL.",
        resume_context=sample_resume_context(),
    )

    assert result["is_safe"] is True


def test_detects_new_numeric_claim():
    result = validate_rewrite(
        original="Built a Flask REST API.",
        rewritten="Built a Flask REST API serving 500 users.",
        resume_context=sample_resume_context(),
    )

    assert result["is_safe"] is False
    assert "500" in result["new_numeric_claims"]


def test_existing_number_is_allowed():
    result = validate_rewrite(
        original="Built an API used by 500 users.",
        rewritten="Built a Flask API used by 500 users.",
        resume_context=sample_resume_context(),
    )

    assert result["new_numeric_claims"] == []


def test_find_unsupported_keywords():
    unsupported = find_unsupported_keywords(
        "Built a Flask API.",
        "Built a Flask API using Docker.",
        resume_context=sample_resume_context(),
    )

    assert "docker" in unsupported


def test_find_new_numeric_claims():
    numbers = find_new_numeric_claims(
        "Built an API.",
        "Built an API used by 100 users.",
    )

    assert numbers == ["100"]


def test_empty_original_is_rejected():
    try:
        validate_rewrite(
            original="",
            rewritten="Built a Flask API.",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Original content cannot be empty" in str(exc)


def test_empty_rewrite_is_rejected():
    try:
        validate_rewrite(
            original="Built a Flask API.",
            rewritten="",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Rewritten content cannot be empty" in str(exc)
        
        
def test_generic_resume_wording_is_not_flagged():
    original = (
        "Implemented PDF parsing using PDFPlumber "
        "to extract and process resume data automatically."
    )

    rewritten = (
        "Automated resume data extraction and processing "
        "by implementing a PDF parsing workflow using "
        "Python and PDFPlumber."
    )

    resume_context = {
        "skills": {
            "technical": ["Python", "PDFPlumber"],
        }
    }

    result = validate_rewrite(
        original=original,
        rewritten=rewritten,
        resume_context=resume_context,
    )

    assert result["is_safe"] is True
    assert result["unsupported_keywords"] == []
    

def test_new_technology_is_still_flagged():
    original = (
        "Implemented PDF parsing using PDFPlumber "
        "to extract and process resume data."
    )

    rewritten = (
        "Implemented PDF parsing using PDFPlumber "
        "and Kubernetes to process resume data."
    )

    result = validate_rewrite(
        original=original,
        rewritten=rewritten,
    )

    assert result["is_safe"] is False
    assert "kubernetes" in result["unsupported_keywords"]


def test_new_numeric_claim_is_still_flagged():
    original = (
        "Implemented PDF parsing using PDFPlumber "
        "to extract and process resume data."
    )

    rewritten = (
        "Implemented PDF parsing using PDFPlumber "
        "to process 50000 resumes."
    )

    result = validate_rewrite(
        original=original,
        rewritten=rewritten,
    )

    assert result["is_safe"] is False
    assert "50000" in result["new_numeric_claims"]