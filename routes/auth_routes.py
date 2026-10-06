from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import get_db_connection
import json
import re

auth = Blueprint("auth", __name__)


@auth.route("/")
def landing():
    return render_template("landing.html")


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validate email format
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        existing_user = cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing_user:

            flash("Email already exists.", "danger")
            conn.close()

            return redirect(url_for("auth.register"))

        cursor.execute("""
            INSERT INTO users(full_name, email, password)
            VALUES(?,?,?)
        """, (full_name, email, hashed_password))

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]

            flash("Login Successful!", "success")

            return redirect(url_for("auth.dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("auth/login.html")



    
    if "user_id" not in session:

        flash("Please login first.", "danger")
        return redirect(url_for("auth.login"))

    return f"""

    <h1>Welcome {session['user_name']}</h1>

    <h3>Email : {session['user_email']}</h3>

    <a href="/logout">Logout</a>

    """


@auth.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        flash("Please login first.", "danger")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    conn = get_db_connection()

    # ---------------------------------------------------------
    # Recent resumes
    # ---------------------------------------------------------

    resumes = conn.execute("""
        SELECT id, title, completion, updated_at
        FROM resumes
        WHERE user_id=?
        ORDER BY updated_at DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    total_resumes = conn.execute(
        "SELECT COUNT(*) AS count FROM resumes WHERE user_id=?",
        (user_id,)
    ).fetchone()["count"]

    average_completion = conn.execute(
        """
        SELECT COALESCE(ROUND(AVG(completion)), 0) AS value
        FROM resumes
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()["value"]

    last_resume_completion = (
        resumes[0]["completion"]
        if resumes
        else 0
    )

    # ---------------------------------------------------------
    # ATS statistics
    # ---------------------------------------------------------

    total_analyses = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM ats_analyses
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()["count"]

    highest_ats_row = conn.execute(
        """
        SELECT MAX(score) AS value
        FROM ats_analyses
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()

    highest_ats_score = (
        highest_ats_row["value"]
        if highest_ats_row and highest_ats_row["value"] is not None
        else 0
    )

    # ---------------------------------------------------------
    # Latest ATS analysis
    # ---------------------------------------------------------

    latest_ats = conn.execute("""
        SELECT
            id,
            resume_id,
            resume_title,
            score,
            analysis_json,
            created_at
        FROM ats_analyses
        WHERE user_id=?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    # Default dashboard values
    ats_overview = {
        "has_analysis": False,
        "analysis_id": None,
        "resume_id": None,
        "resume_title": "",
        "overall_score": 0,
        "keyword_match": 0,
        "formatting": 0,
        "content": 0,
        "skills": 0,
        "created_at": None,
    }

    if latest_ats:

        try:
            analysis = json.loads(
                latest_ats["analysis_json"]
            )

        except (TypeError, json.JSONDecodeError):
            analysis = {}

        score_data = analysis.get("score") or {}

        component_scores = (
            score_data.get("component_scores") or {}
        )

        # -----------------------------------------------------
        # Helper for safe numeric values
        # -----------------------------------------------------

        def valid_score(value):
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )

        def average_scores(*values):
            valid_values = [
                float(value)
                for value in values
                if valid_score(value)
            ]

            if not valid_values:
                return 0

            return round(
                sum(valid_values) / len(valid_values)
            )

        # -----------------------------------------------------
        # Dashboard metric mapping
        # -----------------------------------------------------

        keyword_match = component_scores.get(
            "technical_keywords"
        )

        formatting = component_scores.get(
            "parseability"
        )

        content = average_scores(
            component_scores.get("practical_experience"),
            component_scores.get("responsibilities"),
            component_scores.get("education"),
        )

        skills = average_scores(
            component_scores.get("required_skills"),
            component_scores.get("preferred_skills"),
        )

        # -----------------------------------------------------
        # Final dashboard object
        # -----------------------------------------------------

        ats_overview = {
            "has_analysis": True,

            "analysis_id": latest_ats["id"],

            "resume_id": latest_ats["resume_id"],

            "resume_title": (
                latest_ats["resume_title"]
                or "Untitled Resume"
            ),

            "overall_score": round(
                float(latest_ats["score"] or 0)
            ),

            "keyword_match": (
                round(float(keyword_match))
                if valid_score(keyword_match)
                else 0
            ),

            "formatting": (
                round(float(formatting))
                if valid_score(formatting)
                else 0
            ),

            "content": content,

            "skills": skills,

            "created_at": latest_ats["created_at"],
        }

    conn.close()

    return render_template(
        "dashboard/dashboard.html",

        user_name=session["user_name"],

        user_email=session["user_email"],

        page_title="Dashboard",

        resumes=resumes,

        total_resumes=total_resumes,

        average_completion=average_completion,

        last_resume_completion=last_resume_completion,

        total_analyses=total_analyses,

        highest_ats_score=highest_ats_score,

        ats_overview=ats_overview
    )
    
    
@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))