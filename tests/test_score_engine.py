from ats.score_engine import (
    DEFAULT_WEIGHTS,
    calculate_component_scores,
    calculate_ats_score,
    build_score_summary,
    get_score_level,
)


def test_default_weights_equal_100():
    assert sum(DEFAULT_WEIGHTS.values()) == 100

    assert DEFAULT_WEIGHTS["required_skills"] == 30
    assert DEFAULT_WEIGHTS["technical_keywords"] == 15
    assert DEFAULT_WEIGHTS["practical_experience"] == 20
    assert DEFAULT_WEIGHTS["responsibilities"] == 15
    assert DEFAULT_WEIGHTS["parseability"] == 10
    assert DEFAULT_WEIGHTS["education"] == 5
    assert DEFAULT_WEIGHTS["preferred_skills"] == 5


def test_component_score_calculation():
    match_analysis = {
        "required_skills": {
            "matched": ["Python", "Flask"],
            "missing": ["Docker"],
        },
        "technical_keywords": {
            "matched": ["Python", "Flask", "PostgreSQL"],
            "missing": ["Docker"],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": ["Manage infrastructure"],
        },
        "experience": {
            "matched": ["3 years experience"],
            "missing": [],
        },
        "education": {
            "matched": [],
            "missing": ["Bachelor's degree"],
        },
        "preferred_skills": {
            "matched": ["React"],
            "missing": ["AWS"],
        },
    }

    scores = calculate_component_scores(
        match_analysis,
        parseability_analysis={
            "score": 90,
        },
    )

    assert round(scores["required_skills"], 2) == 66.67
    assert scores["technical_keywords"] == 75.0
    assert scores["practical_experience"] == 100.0
    assert scores["responsibilities"] == 50.0
    assert scores["parseability"] == 90.0
    assert scores["education"] == 0.0
    assert scores["preferred_skills"] == 50.0


def test_final_score_is_between_zero_and_100():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": ["Docker"],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": ["Docker"],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "experience": {
            "matched": ["3 years"],
            "missing": [],
        },
        "education": {
            "matched": ["Bachelor's"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": ["React"],
            "missing": [],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        parseability_analysis={
            "score": 80,
        },
    )

    assert 0 <= result["score"] <= 100


def test_perfect_match_produces_100():
    match_analysis = {
        "required_skills": {
            "matched": ["Python", "Flask"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python", "Flask"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "experience": {
            "matched": ["3 years"],
            "missing": [],
        },
        "education": {
            "matched": ["Bachelor's"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": ["React"],
            "missing": [],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        parseability_analysis={
            "score": 100,
        },
    )

    assert result["score"] == 100.0


def test_zero_match_produces_zero():
    match_analysis = {
        "required_skills": {
            "matched": [],
            "missing": ["Python", "Flask"],
        },
        "technical_keywords": {
            "matched": [],
            "missing": ["Python", "Flask"],
        },
        "responsibilities": {
            "matched": [],
            "missing": ["Build APIs"],
        },
        "experience": {
            "matched": [],
            "missing": ["3 years"],
        },
        "education": {
            "matched": [],
            "missing": ["Bachelor's"],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["React"],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        parseability_analysis={
            "score": 0,
        },
    )

    assert result["score"] == 0.0


def test_empty_categories_are_not_penalized():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "experience": {
            "matched": [],
            "missing": [],
        },
        "education": {
            "matched": [],
            "missing": [],
        },
        "preferred_skills": {
            "matched": [],
            "missing": [],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        parseability_analysis={
            "score": 100,
        },
    )

    assert result["score"] == 100.0


def test_custom_weights():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": ["Docker"],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": ["Docker"],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        weights={
            "required_skills": 80,
            "technical_keywords": 20,
        },
    )

    assert result["score"] == 50.0


def test_score_level():
    assert get_score_level(90) == "Excellent"
    assert get_score_level(75) == "Strong"
    assert get_score_level(60) == "Moderate"
    assert get_score_level(45) == "Needs Improvement"
    assert get_score_level(20) == "Weak"


def test_score_summary():
    score_result = {
        "score": 82.5,
        "component_scores": {
            "required_skills": 80,
            "technical_keywords": 90,
            "practical_experience": 75,
            "responsibilities": 60,
            "parseability": 95,
            "education": 100,
        },
    }

    summary = build_score_summary(
        score_result
    )

    assert summary["score"] == 82.5
    assert summary["level"] == "Strong"
    assert summary["strongest_component"] == "education"
    assert summary["weakest_component"] == "responsibilities"


def test_parseability_is_clamped():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
    }

    high = calculate_component_scores(
        match_analysis,
        parseability_analysis={"score": 150},
    )

    low = calculate_component_scores(
        match_analysis,
        parseability_analysis={"score": -20},
    )

    assert high["parseability"] == 100.0
    assert low["parseability"] == 0.0


def test_invalid_match_analysis_raises_error():
    try:
        calculate_ats_score("invalid")
        assert False, "Expected ValueError"
    except ValueError:
        pass
    

def test_missing_required_skill_hurts_more_than_missing_preferred_skill():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": ["Flask"],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "practical_experience": {
            "matched": ["Project"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "education": {
            "matched": ["Computer Science"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": ["AWS"],
            "missing": ["Docker"],
        },
    }

    parseability = {
        "score": 100,
    }

    result = calculate_ats_score(
        match_analysis,
        resume_analysis={
            "experience": [],
            "projects": [{"name": "Project"}],
            "certifications": [],
        },
        parseability_analysis=parseability,
    )

    assert result["score"] < 100
    assert result["component_scores"]["required_skills"] == 50
    assert result["component_scores"]["preferred_skills"] == 50


def test_preferred_skill_can_improve_score():
    base_match = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "practical_experience": {
            "matched": ["Project"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "education": {
            "matched": ["Computer Science"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["AWS"],
        },
    }

    strong_match = {
        **base_match,
        "preferred_skills": {
            "matched": ["AWS"],
            "missing": [],
        },
    }

    parseability = {
        "score": 100,
    }

    resume = {
        "experience": [],
        "projects": [{"name": "Project"}],
        "certifications": [],
    }

    weak_preferred = calculate_ats_score(
        base_match,
        resume_analysis=resume,
        parseability_analysis=parseability,
    )

    strong_preferred = calculate_ats_score(
        strong_match,
        resume_analysis=resume,
        parseability_analysis=parseability,
    )

    assert (
        strong_preferred["score"]
        > weak_preferred["score"]
    )


def test_parseability_affects_final_score():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "practical_experience": {
            "matched": ["Project"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "education": {
            "matched": ["Computer Science"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": ["AWS"],
            "missing": [],
        },
    }

    resume = {
        "experience": [],
        "projects": [{"name": "Project"}],
        "certifications": [],
    }

    good_parseability = calculate_ats_score(
        match_analysis,
        resume_analysis=resume,
        parseability_analysis={
            "score": 100,
        },
    )

    poor_parseability = calculate_ats_score(
        match_analysis,
        resume_analysis=resume,
        parseability_analysis={
            "score": 0,
        },
    )

    assert (
        good_parseability["score"]
        > poor_parseability["score"]
    )


def test_no_preferred_skills_does_not_reduce_score():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "practical_experience": {
            "matched": ["Project"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "education": {
            "matched": ["Computer Science"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": [],
            "missing": [],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        resume_analysis={
            "experience": [],
            "projects": [{"name": "Project"}],
            "certifications": [],
        },
        parseability_analysis={
            "score": 100,
        },
    )

    assert (
        result["component_scores"]["preferred_skills"]
        is None
    )

    assert result["score"] > 0


def test_student_project_experience_is_counted():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "responsibilities": {
            "matched": [],
            "missing": [],
        },
        "education": {
            "matched": ["Computer Science"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": [],
            "missing": [],
        },
        "experience": {
            "matched": [],
            "missing": [],
        },
    }

    resume_analysis = {
        "experience": [],
        "projects": [
            {
                "name": "Resume Analyzer",
                "description": "Built a Python application.",
            }
        ],
        "certifications": [],
    }

    result = calculate_ats_score(
        match_analysis,
        resume_analysis=resume_analysis,
        parseability_analysis={
            "score": 90,
        },
    )

    assert (
        result["component_scores"]["practical_experience"]
        == 80
    )


def test_score_never_exceeds_100():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": [],
        },
        "technical_keywords": {
            "matched": ["Python"],
            "missing": [],
        },
        "practical_experience": {
            "matched": ["Project"],
            "missing": [],
        },
        "responsibilities": {
            "matched": ["Build APIs"],
            "missing": [],
        },
        "education": {
            "matched": ["Computer Science"],
            "missing": [],
        },
        "preferred_skills": {
            "matched": ["AWS"],
            "missing": [],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        resume_analysis={
            "experience": [{"company": "Example"}],
            "projects": [{"name": "Project"}],
            "certifications": [{"name": "Certification"}],
        },
        parseability_analysis={
            "score": 100,
        },
    )

    assert result["score"] <= 100


def test_score_never_goes_below_zero():
    match_analysis = {
        "required_skills": {
            "matched": [],
            "missing": ["Python"],
        },
        "technical_keywords": {
            "matched": [],
            "missing": ["Python"],
        },
        "practical_experience": {
            "matched": [],
            "missing": ["Experience"],
        },
        "responsibilities": {
            "matched": [],
            "missing": ["Build APIs"],
        },
        "education": {
            "matched": [],
            "missing": ["Computer Science"],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["AWS"],
        },
    }

    result = calculate_ats_score(
        match_analysis,
        resume_analysis={
            "experience": [],
            "projects": [],
            "certifications": [],
        },
        parseability_analysis={
            "score": 0,
        },
    )

    assert result["score"] >= 0