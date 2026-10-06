from ats.normalizer import normalize_resume_state, normalize_term


def test_normalize_term_preserves_common_tech_tokens():
    assert normalize_term("C++") == "c++"
    assert normalize_term("C#") == "c#"
    assert normalize_term("  Python   ") == "python"


def test_normalizer_does_not_mutate_resume_state():
    state = {
        "title": "Test",
        "personal": {"fullName": "Rushi", "headline": "Developer"},
        "summary": "Python developer",
        "skills": {
            "languages": ["Python"],
            "frameworks": ["Flask"],
            "databases": ["MySQL"],
            "tools": ["Git"],
            "others": [],
        },
        "education": [],
        "experience": [],
        "projects": [{
            "title": "Notes",
            "technologies": ["Python", "Flask"],
            "bullets": ["Built CRUD application."],
        }],
        "certifications": [],
        "additionalSections": [],
    }

    normalized = normalize_resume_state(state)

    assert state["skills"]["languages"] == ["Python"]
    assert normalized["skills"]["languages"] == ["Python"]
    assert normalized["stats"]["skill_count"] == 4
    assert "Python developer" in normalized["searchable_text"]
    assert "Built CRUD application." in normalized["searchable_text"]


def test_empty_state_is_safe():
    result = normalize_resume_state({})
    assert result["searchable_text"] == ""
    assert result["stats"]["word_count"] == 0
