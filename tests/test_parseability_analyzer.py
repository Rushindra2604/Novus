from ats.parseability_analyzer import analyze_parseability


def make_resume_analysis():
    return {
        "personal": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+91 9876543210",
        },
        "summary": "Python developer.",
        "education": [
            {
                "degree": "B.Tech",
                "institution": "University",
            }
        ],
        "skills": {
            "languages": ["Python"],
            "frameworks": ["Flask"],
        },
        "experience": [
            {
                "company": "Example",
                "role": "Developer",
                "description": "Built web applications.",
            }
        ],
        "projects": [
            {
                "name": "Project",
                "description": "Built a Python application.",
            }
        ],
        "certifications": [],
    }


def make_resume_text():
    return """
John Doe
john@example.com
+91 9876543210

SUMMARY
Python developer with experience building web applications.

SKILLS
Python
Flask
SQL
Git

EXPERIENCE
Developer
Example Company
2024 - 2025
- Built web applications.
- Debugged application issues.

PROJECTS
Resume Analyzer
2025
- Built a Python application.
- Integrated Flask APIs.

EDUCATION
B.Tech Computer Science
Example University
2021 - 2025

CERTIFICATIONS
Python Certification
"""


def test_parseability_returns_structured_result():
    result = analyze_parseability(
        make_resume_text(),
        make_resume_analysis(),
    )

    assert result["schema_version"] == "1.0"
    assert 0 <= result["score"] <= 100
    assert "checks" in result
    assert "stats" in result


def test_well_structured_resume_scores_well():
    result = analyze_parseability(
        make_resume_text(),
        make_resume_analysis(),
    )

    assert result["score"] >= 80
    assert result["status"] in {
        "excellent",
        "good",
    }


def test_empty_resume_scores_poorly():
    result = analyze_parseability(
        "",
        {},
    )

    assert result["score"] < 50
    assert result["checks"]["text_extractability"]["status"] == "fail"


def test_contact_information_is_detected():
    result = analyze_parseability(
        make_resume_text(),
        make_resume_analysis(),
    )

    assert (
        result["checks"]["contact_information"]["score"]
        == 100
    )


def test_sections_are_detected():
    result = analyze_parseability(
        make_resume_text(),
        make_resume_analysis(),
    )

    sections = result["detected_sections"]

    assert sections["summary"] is True
    assert sections["skills"] is True
    assert sections["experience"] is True
    assert sections["projects"] is True
    assert sections["education"] is True


def test_bullet_count_is_recorded():
    result = analyze_parseability(
        make_resume_text(),
        make_resume_analysis(),
    )

    assert result["stats"]["bullet_count"] >= 4