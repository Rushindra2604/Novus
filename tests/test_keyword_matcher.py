from ats.keyword_matcher import (
    match_terms,
    match_responsibilities,
    build_match_analysis,
)


def test_exact_skill_matching():
    result = match_terms(
        ["Python", "Flask", "Git"],
        ["Python", "Flask"],
    )

    assert result["matched"] == ["Python", "Flask"]
    assert result["missing"] == []


def test_missing_skill_detection():
    result = match_terms(
        ["Python", "Flask"],
        ["Python", "Flask", "Docker"],
    )

    assert result["matched"] == ["Python", "Flask"]
    assert result["missing"] == ["Docker"]


def test_case_insensitive_matching():
    result = match_terms(
        ["python", "FLASK"],
        ["Python", "Flask"],
    )

    assert result["matched"] == ["Python", "Flask"]
    assert result["missing"] == []


def test_common_aliases_match():
    result = match_terms(
        [
            "React.js",
            "Node.js",
            "Postgres",
            "JavaScript",
        ],
        [
            "React",
            "Node",
            "PostgreSQL",
            "JavaScript",
        ],
    )

    assert result["matched"] == [
        "React",
        "Node",
        "PostgreSQL",
        "JavaScript",
    ]

    assert result["missing"] == []


def test_cplusplus_and_csharp_are_preserved():
    result = match_terms(
        ["C++", "C#"],
        ["C++", "C#"],
    )

    assert result["matched"] == ["C++", "C#"]


def test_duplicate_resume_terms_do_not_change_result():
    result = match_terms(
        ["Python", "Python", "python"],
        ["Python"],
    )

    assert result["matched"] == ["Python"]
    assert result["missing"] == []


def test_responsibility_matching():
    resume_text = """
    Developed REST APIs using Python and Flask.
    Built backend services and debugged production issues.
    """

    responsibilities = [
        "Develop REST APIs using Python",
        "Debug production issues",
        "Manage Kubernetes infrastructure",
    ]

    result = match_responsibilities(
        resume_text,
        responsibilities,
    )

    assert "Develop REST APIs using Python" in result["matched"]
    assert "Debug production issues" in result["matched"]
    assert "Manage Kubernetes infrastructure" in result["missing"]


def test_build_match_analysis():
    resume = {
        "skills": {
            "languages": ["Python", "JavaScript"],
            "frameworks": ["Flask", "React"],
            "databases": ["PostgreSQL"],
            "tools": ["Git"],
            "others": [],
        },
        "searchable_text": """
        Python Flask React PostgreSQL Git
        Developed REST APIs using Python.
        """,
        "education": [],
        "experience": [],
    }

    jd = {
        "required_skills": [
            "Python",
            "Flask",
            "Docker",
        ],
        "preferred_skills": [
            "React",
            "AWS",
        ],
        "technical_keywords": [
            "Python",
            "Flask",
            "Docker",
            "PostgreSQL",
        ],
        "responsibilities": [
            "Develop REST APIs using Python",
        ],
        "education_requirements": [],
        "experience_requirements": [],
    }

    result = build_match_analysis(
        resume,
        jd,
    )

    assert "Python" in result["required_skills"]["matched"]
    assert "Flask" in result["required_skills"]["matched"]

    assert "Docker" in result["required_skills"]["missing"]

    assert "React" in result["preferred_skills"]["matched"]
    assert "AWS" in result["preferred_skills"]["missing"]

    assert "PostgreSQL" in result["technical_keywords"]["matched"]


def test_match_analysis_stats():
    resume = {
        "skills": {
            "languages": ["Python"],
            "frameworks": [],
            "databases": [],
            "tools": [],
            "others": [],
        },
        "searchable_text": "Python developer",
        "education": [],
        "experience": [],
    }

    jd = {
        "required_skills": ["Python", "Docker"],
        "preferred_skills": ["AWS"],
        "technical_keywords": ["Python", "Docker"],
        "responsibilities": [],
        "education_requirements": [],
        "experience_requirements": [],
    }

    result = build_match_analysis(
        resume,
        jd,
    )

    assert result["stats"]["required_matched"] == 1
    assert result["stats"]["required_missing"] == 1

    assert result["stats"]["preferred_matched"] == 0
    assert result["stats"]["preferred_missing"] == 1


def test_invalid_resume_analysis_raises_error():
    jd = {}

    try:
        build_match_analysis(
            "invalid",
            jd,
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_invalid_jd_analysis_raises_error():
    resume = {}

    try:
        build_match_analysis(
            resume,
            "invalid",
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass
    
    
def test_responsibility_overlap_is_based_on_responsibility_tokens():
    resume = """
    Built and deployed a full-stack web application using Python and Flask.
    Implemented Flask routes for server-side requests.
    Integrated MySQL database for structured data storage.
    Added input validation and error handling.
    """

    responsibilities = [
        "Build web applications.",
    ]

    result = match_responsibilities(
        resume,
        responsibilities,
    )

    assert result["matched"] == [
        "Build web applications."
    ]

    assert result["missing"] == []
    

def test_responsibility_matching_finds_database_evidence():
    resume = """
    Implemented complete CRUD functionality with SQL-based data storage.
    Designed database structures and queries to maintain data consistency.
    """

    responsibilities = [
        "Work with databases.",
    ]

    result = match_responsibilities(
        resume,
        responsibilities,
    )

    assert result["matched"] == [
        "Work with databases."
    ]

    assert result["missing"] == []
    
    
def test_responsibility_matching_rejects_unsupported_responsibility():
    resume = """
    Built web applications using Python and Flask.
    Worked with MySQL databases and SQL-based data storage.
    """

    responsibilities = [
        "Develop Java microservices using Spring Boot.",
    ]

    result = match_responsibilities(
        resume,
        responsibilities,
    )

    assert result["matched"] == []
    assert result["missing"] == [
        "Develop Java microservices using Spring Boot."
    ]
    
    
def test_sql_requirement_is_supported_by_mysql():
    result = match_terms(
        ["Python", "MySQL"],
        ["SQL"],
    )

    assert result["matched"] == ["SQL"]
    assert result["missing"] == []
    
    
def test_mysql_requirement_is_not_supported_by_generic_sql():
    result = match_terms(
        ["Python", "SQL"],
        ["MySQL"],
    )

    assert result["matched"] == []
    assert result["missing"] == ["MySQL"]
    
    
def test_ai_api_requirement_is_supported_by_gemini_api():
    result = match_terms(
        ["Python", "Google Gemini API"],
        ["AI APIs"],
    )

    assert result["matched"] == ["AI APIs"]
    assert result["missing"] == []
    
    
def test_pdf_parsing_is_supported_by_pdfplumber():
    result = match_terms(
        ["Python", "PDFPlumber"],
        ["PDF parsing"],
    )

    assert result["matched"] == ["PDF parsing"]
    assert result["missing"] == []
    
    
def test_cloud_deployment_is_supported_by_render():
    result = match_terms(
        ["Python", "Render"],
        ["Cloud deployment"],
    )

    assert result["matched"] == ["Cloud deployment"]
    assert result["missing"] == []
    
    
def test_cloud_deployment_does_not_prove_aws():
    result = match_terms(
        ["Python", "Render"],
        ["AWS"],
    )

    assert result["matched"] == []
    assert result["missing"] == ["AWS"]