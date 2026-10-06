from ats.jd_parser import parse_job_description


def test_parse_job_description_extracts_title():
    jd = """
    Job Title: Python Developer

    We are looking for a software developer.
    """

    result = parse_job_description(jd)

    assert result["title"] == "Python Developer"


def test_extracts_technical_keywords():
    jd = """
    Requirements:
    - Strong Python experience
    - Experience with Flask and PostgreSQL
    - Knowledge of Docker and Git
    """

    result = parse_job_description(jd)

    assert "python" in result["technical_keywords"]
    assert "flask" in result["technical_keywords"]
    assert "postgresql" in result["technical_keywords"]
    assert "docker" in result["technical_keywords"]
    assert "git" in result["technical_keywords"]


def test_classifies_required_and_preferred_requirements():
    jd = """
    Requirements:
    - Required: Python
    - Must have experience with Flask
    - Strong communication skills

    Preferred Qualifications:
    - Preferred: Docker
    - Nice to have: AWS
    """

    result = parse_job_description(jd)

    assert "Required: Python" in result["required_skills"]
    assert "Must have experience with Flask" in result["required_skills"]

    assert "Preferred: Docker" in result["preferred_skills"]
    assert "Nice to have: AWS" in result["preferred_skills"]


def test_extracts_responsibilities():
    jd = """
    Responsibilities:
    - Build backend services
    - Develop REST APIs
    - Debug production issues
    """

    result = parse_job_description(jd)

    assert "Build backend services" in result["responsibilities"]
    assert "Develop REST APIs" in result["responsibilities"]
    assert "Debug production issues" in result["responsibilities"]


def test_extracts_experience_requirement():
    jd = """
    Requirements:
    - 2+ years of experience with Python
    - Strong communication skills
    """

    result = parse_job_description(jd)

    assert len(result["experience_requirements"]) >= 1
    assert any(
        "2+ years" in item
        for item in result["experience_requirements"]
    )


def test_extracts_education_requirement():
    jd = """
    Education:
    Bachelor's degree in Computer Science or related field.
    """

    result = parse_job_description(jd)

    assert len(result["education_requirements"]) >= 1
    assert any(
        "Bachelor" in item
        for item in result["education_requirements"]
    )


def test_preserves_raw_job_description():
    jd = """
    Python Developer

    Requirements:
    - Python
    - Flask
    """

    result = parse_job_description(jd)

    assert result["source"]["raw_text"] == jd.strip()


def test_parser_does_not_modify_input():
    jd = """
    Requirements:
    - Python
    - Flask
    """

    original = jd

    parse_job_description(jd)

    assert jd == original


def test_empty_job_description_raises_error():
    try:
        parse_job_description("")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_stats_are_consistent():
    jd = """
    Job Title: Backend Developer

    Responsibilities:
    - Build APIs
    - Maintain services

    Requirements:
    - Required: Python
    - 2+ years of experience

    Preferred Qualifications:
    - Nice to have: AWS
    """

    result = parse_job_description(jd)

    assert result["stats"]["required_count"] == len(
        result["required_skills"]
    )

    assert result["stats"]["preferred_count"] == len(
        result["preferred_skills"]
    )

    assert result["stats"]["technical_keyword_count"] == len(
        result["technical_keywords"]
    )

    assert result["stats"]["responsibility_count"] == len(
        result["responsibilities"]
    )
    
def test_required_skills_are_extracted_from_required_section():
    jd = """
    Backend Developer

    Required Skills:
    Python
    Flask
    SQL
    Git
    """

    result = parse_job_description(jd)

    assert "python" in result["required_skills"]
    assert "flask" in result["required_skills"]
    assert "sql" in result["required_skills"]
    assert "git" in result["required_skills"]


def test_preferred_skills_are_extracted_from_preferred_section():
    jd = """
    Backend Developer

    Required Skills:
    Python
    Flask

    Preferred Skills:
    AWS
    Docker
    """

    result = parse_job_description(jd)

    assert any(
        skill.lower() == "python"
        for skill in result["required_skills"]
    )

    assert any(
        skill.lower() == "flask"
        for skill in result["required_skills"]
    )

    assert any(
        skill.lower() == "aws"
        for skill in result["preferred_skills"]
    )

    assert any(
        skill.lower() == "docker"
        for skill in result["preferred_skills"]
    )


def test_preferred_skills_are_not_required():
    jd = """
    Backend Developer

    Required Skills:
    Python
    Flask

    Preferred Skills:
    AWS
    Docker
    """

    result = parse_job_description(jd)

    assert "aws" not in result["required_skills"]
    assert "docker" not in result["required_skills"]


def test_required_skills_can_be_embedded_in_requirement_sentence():
    jd = """
    Backend Developer

    Requirements:
    Strong experience with Python and Flask.
    Knowledge of SQL and Git.
    """

    result = parse_job_description(jd)

    assert "python" in result["required_skills"]
    assert "flask" in result["required_skills"]
    assert "sql" in result["required_skills"]
    assert "git" in result["required_skills"]