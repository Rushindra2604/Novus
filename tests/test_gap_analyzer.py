from ats.gap_analyzer import (
    build_gap_analysis,
    build_gap_summary,
)


def test_required_skill_gap_is_critical():
    match_analysis = {
        "required_skills": {
            "matched": ["Python"],
            "missing": ["Docker"],
        }
    }

    result = build_gap_analysis(
        match_analysis
    )

    assert len(result["gaps"]) == 1

    gap = result["gaps"][0]

    assert gap["item"] == "Docker"
    assert gap["category"] == "required_skill"
    assert gap["priority"] == "critical"


def test_preferred_skill_gap_is_medium():
    match_analysis = {
        "preferred_skills": {
            "matched": ["React"],
            "missing": ["AWS"],
        }
    }

    result = build_gap_analysis(
        match_analysis
    )

    gap = result["gaps"][0]

    assert gap["item"] == "AWS"
    assert gap["category"] == "preferred_skill"
    assert gap["priority"] == "medium"


def test_technical_keyword_gap_is_high():
    match_analysis = {
        "technical_keywords": {
            "matched": ["Python"],
            "missing": ["Docker"],
        }
    }

    result = build_gap_analysis(
        match_analysis
    )

    gap = result["gaps"][0]

    assert gap["item"] == "Docker"
    assert gap["category"] == "technical_keyword"
    assert gap["priority"] == "high"


def test_responsibility_gap_is_high():
    match_analysis = {
        "responsibilities": {
            "matched": [],
            "missing": [
                "Manage Kubernetes infrastructure"
            ],
        }
    }

    result = build_gap_analysis(
        match_analysis
    )

    gap = result["gaps"][0]

    assert gap["category"] == "responsibility"
    assert gap["priority"] == "high"


def test_experience_gap_is_critical():
    match_analysis = {
        "experience": {
            "matched": [],
            "missing": [
                "3+ years of experience"
            ],
        }
    }

    result = build_gap_analysis(
        match_analysis
    )

    gap = result["gaps"][0]

    assert gap["category"] == "experience"
    assert gap["priority"] == "critical"


def test_education_gap_is_critical():
    match_analysis = {
        "education": {
            "matched": [],
            "missing": [
                "Bachelor's degree in Computer Science"
            ],
        }
    }

    result = build_gap_analysis(
        match_analysis
    )

    gap = result["gaps"][0]

    assert gap["category"] == "education"
    assert gap["priority"] == "critical"


def test_gaps_are_sorted_by_priority():
    match_analysis = {
        "required_skills": {
            "matched": [],
            "missing": ["Docker"],
        },
        "technical_keywords": {
            "matched": [],
            "missing": ["Kubernetes"],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["AWS"],
        },
    }

    result = build_gap_analysis(
        match_analysis
    )

    assert result["gaps"][0]["priority"] == "critical"
    assert result["gaps"][1]["priority"] == "high"
    assert result["gaps"][2]["priority"] == "medium"


def test_duplicate_gap_keeps_highest_priority():
    match_analysis = {
        "required_skills": {
            "matched": [],
            "missing": ["Docker"],
        },
        "technical_keywords": {
            "matched": [],
            "missing": ["Docker"],
        },
    }

    result = build_gap_analysis(
        match_analysis
    )

    assert len(result["gaps"]) == 2

    priorities = [
        gap["priority"]
        for gap in result["gaps"]
    ]

    assert priorities == [
        "critical",
        "critical",
    ]


def test_gap_stats_are_correct():
    match_analysis = {
        "required_skills": {
            "matched": [],
            "missing": ["Docker"],
        },
        "technical_keywords": {
            "matched": [],
            "missing": ["Kubernetes"],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["AWS"],
        },
    }

    result = build_gap_analysis(
        match_analysis
    )

    assert result["stats"]["total_gaps"] == 3
    assert result["stats"]["critical_count"] == 1
    assert result["stats"]["high_count"] == 1
    assert result["stats"]["medium_count"] == 1


def test_gap_summary():
    match_analysis = {
        "required_skills": {
            "matched": [],
            "missing": [
                "Docker",
                "Kubernetes",
            ],
        },
        "technical_keywords": {
            "matched": [],
            "missing": ["CI/CD"],
        },
        "preferred_skills": {
            "matched": [],
            "missing": ["AWS"],
        },
    }

    gap_analysis = build_gap_analysis(
        match_analysis
    )

    summary = build_gap_summary(
        gap_analysis
    )

    assert summary["total_gaps"] == 4
    assert summary["critical_count"] == 2
    assert summary["high_count"] == 1
    assert summary["has_critical_gaps"] is True

    assert summary["top_priority_gaps"] == [
        "Docker",
        "Kubernetes",
    ]


def test_empty_match_analysis_has_no_gaps():
    result = build_gap_analysis({})

    assert result["gaps"] == []
    assert result["stats"]["total_gaps"] == 0

    summary = build_gap_summary(result)

    assert summary["total_gaps"] == 0
    assert summary["top_priority_gaps"] == []
    assert summary["has_critical_gaps"] is False


def test_invalid_match_analysis_raises_error():
    try:
        build_gap_analysis("invalid")
        assert False, "Expected ValueError"
    except ValueError:
        pass