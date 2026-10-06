from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, json, make_response
from database.database import get_db_connection


from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document

from utils.resume_parser import parse_resume

import io
import re
import os

# ==========================================================
# WEASYPRINT / MSYS2 DLL SETUP
# ==========================================================

MSYS2_BIN = r"C:\msys64\ucrt64\bin"

if os.path.isdir(MSYS2_BIN):
    os.add_dll_directory(MSYS2_BIN)

from weasyprint import HTML

resume = Blueprint("resume", __name__)


def login_required():

    if "user_id" not in session:
        flash("Please login first.", "danger")
        return False
    return True


def has_resume_content(state):
    """Return True only when the state contains actual user-entered resume content."""

    def meaningful(value, key="", is_root=False):

        if isinstance(value, str):
            text = value.strip()

            if not text:
                return False

            if is_root and key == "title" and text == "Untitled Resume":
                return False

            return True

        if isinstance(value, list):
            return any(meaningful(item) for item in value)

        if isinstance(value, dict):
            for child_key, child_value in value.items():

                # Editor metadata is not resume content.
                if child_key in {"id", "type", "visible", "expanded"}:
                    continue

                # Additional-section metadata has a structural title.
                if (
                    not is_root
                    and child_key == "title"
                    and isinstance(child_value, dict)
                    and "type" in child_value
                    and "content" in child_value
                ):
                    continue

                if meaningful(child_value, child_key, False):
                    return True

        return False

    return meaningful(state, "", True)


def normalize_resume_state(state):

    additional_sections = (
        state.get("additionalSections", [])
        or []
    )

    section_order = (
        state.get("sectionOrder", [])
        or []
    )

    if not section_order:

        section_order = [
            "personal",
            "summary",
            "education",
            "skills",
            "projects",
            "experience",
            "certifications"
        ]

    # Make sure imported/custom sections are also
    # included in the PDF section order.
    for item in additional_sections:

        if not isinstance(item, dict):
            continue

        section_id = item.get("id")

        if not section_id:
            continue

        if item.get("visible", True) is False:
            continue

        if section_id not in section_order:
            section_order.append(section_id)

    return {
        "title":
            state.get(
                "title",
                "Untitled Resume"
            ),

        "personal":
            state.get(
                "personal",
                {}
            ) or {},

        "summary":
            state.get(
                "summary",
                ""
            ) or "",

        "education":
            state.get(
                "education",
                []
            ) or [],

        "skills":
            state.get(
                "skills",
                {}
            ) or {},

        "projects":
            state.get(
                "projects",
                []
            ) or [],

        "experience":
            state.get(
                "experience",
                []
            ) or [],

        "certifications":
            state.get(
                "certifications",
                []
            ) or [],

        "additionalSections":
            additional_sections,

        "sectionOrder":
            section_order
    }

    
@resume.route("/my-resumes")
def my_resumes():

    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    resumes = conn.execute("""
    SELECT *
    FROM resumes
    WHERE user_id=?
    ORDER BY updated_at DESC
    """,
    (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template(
        "resume/my_resumes.html",
        page_title="My Resumes",
        user_name=session["user_name"],
        resumes=resumes

    )


@resume.route("/resume/<int:resume_id>/delete", methods=["POST"])
def delete_resume(resume_id):
    """Permanently delete a resume owned by the currently logged-in user."""
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    resume_row = conn.execute("""
        SELECT id
        FROM resumes
        WHERE id=? AND user_id=?
    """, (resume_id, session["user_id"])).fetchone()

    if not resume_row:
        conn.close()
        flash("Resume not found.", "danger")
        return redirect(url_for("resume.my_resumes"))

    # Remove saved ATS analysis snapshots that belong to this resume.
    # The internal resume ID is never renumbered or reused.
    conn.execute("""
        DELETE FROM ats_analyses
        WHERE resume_id=? AND user_id=?
    """, (resume_id, session["user_id"]))

    conn.execute("""
        DELETE FROM resumes
        WHERE id=? AND user_id=?
    """, (resume_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Resume deleted successfully.", "success")
    return redirect(url_for("resume.my_resumes"))


@resume.route("/resume/new")
def new_resume():

    if not login_required():
        return redirect(url_for("auth.login"))

    # Do not create a database resume yet.
    # The resume will be created after the user enters content.
    draft_resume = {
        "id": "",
        "title": "Untitled Resume",
        "personal_info": json.dumps({}),
        "summary": "",
        "education": json.dumps([]),
        "skills": json.dumps({}),
        "projects": json.dumps([]),
        "experience": json.dumps([]),
        "certifications": json.dumps([]),
        "custom_sections": json.dumps([]),
        "completion": 0,
        "source_type": "created",
        "uploaded_filename": "",
        "extracted_text": ""
    }

    return render_template(
        "resume/resume_studio.html",
        page_title="Resume Studio",
        user_name=session["user_name"],
        resume=draft_resume
    )
        

@resume.route("/resume/upload", methods=["POST"])
def upload_resume():
    if not login_required():
        return redirect(url_for("auth.login"))

    file = request.files.get("resume")

    if not file or file.filename == "":
        flash("Please select a resume file.", "danger")
        return redirect(url_for("auth.dashboard"))

    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)[1].lower()

    if extension not in [".pdf", ".docx"]:
        flash("Only PDF and DOCX resumes are supported.", "danger")
        return redirect(url_for("auth.dashboard"))

    try:
        # --------------------------------------------------
        # STEP 1: Extract raw text from uploaded file
        # --------------------------------------------------

        extracted_text = ""

        if extension == ".pdf":
            reader = PdfReader(file)

            for page in reader.pages:
                text = page.extract_text() or ""
                extracted_text += text + "\n"

        elif extension == ".docx":
            document = Document(file)

            for paragraph in document.paragraphs:
                extracted_text += paragraph.text + "\n"

        extracted_text = extracted_text.strip()

        if not extracted_text:
            flash(
                "We couldn't extract any text from this resume.",
                "danger"
            )
            return redirect(url_for("auth.dashboard"))

        # --------------------------------------------------
        # STEP 2: Parse extracted text into Resume Studio
        # --------------------------------------------------

        fallback_title = os.path.splitext(filename)[0]

        parsed_resume = parse_resume(
            extracted_text,
            fallback_title=fallback_title
        )

        # --------------------------------------------------
        # STEP 3: Store parsed resume in database
        # --------------------------------------------------

        conn = get_db_connection()
        cursor = conn.cursor()

        next_number = cursor.execute("""
            SELECT COALESCE(MAX(resume_number), 0) + 1
            FROM resumes
            WHERE user_id=?
        """, (session["user_id"],)).fetchone()[0]

        cursor.execute("""
            INSERT INTO resumes(
                user_id,
                title,
                personal_info,
                summary,
                education,
                skills,
                projects,
                experience,
                certifications,
                custom_sections,
                source_type,
                uploaded_filename,
                extracted_text,
                resume_number
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],

            parsed_resume.get("title") or fallback_title,

            json.dumps(
                parsed_resume.get("personal") or {}
            ),

            parsed_resume.get("summary") or "",

            json.dumps(
                parsed_resume.get("education") or []
            ),

            json.dumps(
                parsed_resume.get("skills") or {}
            ),

            json.dumps(
                parsed_resume.get("projects") or []
            ),

            json.dumps(
                parsed_resume.get("experience") or []
            ),

            json.dumps(
                parsed_resume.get("certifications") or []
            ),

            json.dumps(
                parsed_resume.get("additionalSections") or []
            ),

            "uploaded",

            filename,

            # Keep original extracted text.
            # This is important for future AI parsing/reprocessing.
            extracted_text,

            next_number
        ))

        resume_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # --------------------------------------------------
        # STEP 4: Redirect to Resume Studio
        # --------------------------------------------------

        session["uploaded_resume_text"] = extracted_text
        session["uploaded_resume_id"] = resume_id

        return redirect(
            url_for(
                "resume.resume_studio",
                resume_id=resume_id
            )
        )

    except Exception as e:
        print("Resume upload error:", e)

        flash(
            "Something went wrong while importing your resume.",
            "danger"
        )

        return redirect(url_for("auth.dashboard"))

        
@resume.route("/resume-studio")
def resume_studio_latest():
    """Open the user's most recently updated resume in Resume Studio.

    If the user has no resume yet, start the normal new-resume flow.
    This gives shared navigation a stable Resume Studio destination
    without changing the existing /resume/<id> editor route.
    """
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    row = conn.execute("""
        SELECT id
        FROM resumes
        WHERE user_id=?
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
    """, (session["user_id"],)).fetchone()
    conn.close()

    if row:
        return redirect(url_for("resume.resume_studio", resume_id=row["id"]))

    return redirect(url_for("resume.new_resume"))


@resume.route("/resume/<int:resume_id>")
def resume_studio(resume_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    resume = conn.execute("""

    SELECT *
    FROM resumes
    WHERE
    id=?
    AND
    user_id=?
    """,

    (
        resume_id,
        session["user_id"]
    )

    ).fetchone()
    conn.close()

    if not resume:
        flash("Resume not found.","danger")
        return redirect(url_for("resume.my_resumes"))

    return render_template(
        "resume/resume_studio.html",
        page_title="Resume Studio",
        user_name=session["user_name"],
        resume=resume

    )


@resume.route("/api/resume/create", methods=["POST"])
def create_resume_api():

    if not login_required():
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}
    state = data.get("resume") or {}

    if not isinstance(state, dict):
        return jsonify({
            "success": False,
            "message": "Invalid resume data"
        }), 400

    # Don't create an empty resume.
    meaningful_content = False

    def contains_content(value):

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, list):
            return any(
                contains_content(item)
                for item in value
            )

        if isinstance(value, dict):
            for key, child in value.items():

                if key in {
                    "id",
                    "type",
                    "visible",
                    "expanded"
                }:
                    continue

                if contains_content(child):
                    return True

        return False

    # Ignore the default title.
    state_for_check = dict(state)

    if state_for_check.get("title") == "Untitled Resume":
        state_for_check["title"] = ""

    meaningful_content = contains_content(state_for_check)

    if not meaningful_content:
        return jsonify({
            "success": False,
            "skipped": True,
            "message": "Nothing to save yet."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO resumes(
            user_id,
            title,
            personal_info,
            summary,
            education,
            skills,
            projects,
            experience,
            certifications,
            custom_sections,
            completion,
            source_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],

        state.get("title") or "Untitled Resume",

        json.dumps(
            state.get("personal") or {},
            ensure_ascii=False
        ),

        state.get("summary") or "",

        json.dumps(
            state.get("education") or [],
            ensure_ascii=False
        ),

        json.dumps(
            state.get("skills") or {},
            ensure_ascii=False
        ),

        json.dumps(
            state.get("projects") or [],
            ensure_ascii=False
        ),

        json.dumps(
            state.get("experience") or [],
            ensure_ascii=False
        ),

        json.dumps(
            state.get("certifications") or [],
            ensure_ascii=False
        ),

        json.dumps(
            state.get("additionalSections") or [],
            ensure_ascii=False
        ),

        int(state.get("completion", 0) or 0),

        "created"
    ))

    resume_id = cursor.lastrowid

    conn.commit()

    row = conn.execute("""
        SELECT updated_at
        FROM resumes
        WHERE id=? AND user_id=?
    """, (
        resume_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    return jsonify({
        "success": True,
        "resume_id": resume_id,
        "updated_at": row["updated_at"] if row else None
    })
    
    
@resume.route("/api/resume/save/<int:resume_id>", methods=["POST"])
def save_resume_api(resume_id):

    if not login_required():
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401


    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400


    state = data.get("resume", {})


    if not isinstance(state, dict):

        return jsonify({
            "success": False,
            "message": "Invalid resume data"
        }), 400


    conn = get_db_connection()


    resume_row = conn.execute("""
        SELECT id
        FROM resumes
        WHERE id=? AND user_id=?
    """, (
        resume_id,
        session["user_id"]
    )).fetchone()


    if not resume_row:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Resume not found"
        }), 404


    conn.execute("""
        UPDATE resumes

        SET
            title=?,
            personal_info=?,
            summary=?,
            education=?,
            skills=?,
            projects=?,
            experience=?,
            certifications=?,
            custom_sections=?,
            completion=?,
            updated_at=CURRENT_TIMESTAMP

        WHERE
            id=?
            AND user_id=?
    """, (

        state.get("title", ""),

        json.dumps(
            state.get("personal", {}),
            ensure_ascii=False
        ),

        state.get("summary", ""),

        json.dumps(
            state.get("education", []),
            ensure_ascii=False
        ),

        json.dumps(
            state.get("skills", {}),
            ensure_ascii=False
        ),

        json.dumps(
            state.get("projects", []),
            ensure_ascii=False
        ),

        json.dumps(
            state.get("experience", []),
            ensure_ascii=False
        ),

        json.dumps(
            state.get("certifications", []),
            ensure_ascii=False
        ),

        json.dumps(
            state.get("additionalSections", []),
            ensure_ascii=False
        ),

        int(
            state.get("completion", 0) or 0
        ),

        resume_id,
        session["user_id"]

    ))


    conn.commit()


    updated_row = conn.execute("""
        SELECT updated_at
        FROM resumes
        WHERE id=? AND user_id=?
    """, (
        resume_id,
        session["user_id"]
    )).fetchone()


    conn.close()


    return jsonify({

        "success": True,

        "updated_at":
            updated_row["updated_at"]
            if updated_row
            else None

    })


@resume.route("/api/resume/<int:resume_id>/pdf",methods=["POST"])
def download_resume_pdf(resume_id):

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401


    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "No resume data received"
        }), 400


    state = data.get("resume", {})


    if not isinstance(state, dict):

        return jsonify({
            "success": False,
            "message": "Invalid resume data"
        }), 400


    # --------------------------------------------------
    #  VERIFY RESUME OWNERSHIP
    # --------------------------------------------------

    conn = get_db_connection()

    resume_row = conn.execute("""
        SELECT id, title
        FROM resumes
        WHERE id=? AND user_id=?
    """, (
        resume_id,
        session["user_id"]
    )).fetchone()

    conn.close()


    if not resume_row:

        return jsonify({
            "success": False,
            "message": "Resume not found"
        }), 404


    # --------------------------------------------------
    #   NORMALIZE STATE
    # --------------------------------------------------

    resume_data = normalize_resume_state(
        state
    )


    # --------------------------------------------------
    #  RENDER PDF HTML
    # -------------------------------------------------- 

    try:

        rendered_html = render_template(
            "resume/resume_pdf.html",
            resume=resume_data
        )


        # ------------------------------------------------
        #   GENERATE REAL PDF
        # ------------------------------------------------ 

        pdf_bytes = HTML(
            string=rendered_html,
            base_url=request.url_root
        ).write_pdf()


    except Exception as error:

        print(
            "Resume PDF generation error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate PDF"
        }), 500


    # --------------------------------------------------
    #   SAFE FILENAME
    # --------------------------------------------------

    filename = (
        resume_data.get("title")
        or "Novus Resume"
    )

    filename = re.sub(
        r'[<>:"/\\|?*]+',
        "",
        filename
    ).strip()


    if not filename:

        filename = "Novus Resume"


    response = make_response(
        pdf_bytes
    )


    response.headers[
        "Content-Type"
    ] = "application/pdf"


    response.headers[
        "Content-Disposition"
    ] = (
        f'attachment; filename="{filename}.pdf"'
    )


    return response


@resume.route("/api/resume/load/<int:resume_id>")
def load_resume_api(resume_id):

    if not login_required():
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = get_db_connection()

    resume_row = conn.execute("""
        SELECT *
        FROM resumes
        WHERE id=? AND user_id=?
    """, (
        resume_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if not resume_row:
        return jsonify({
            "success": False,
            "message": "Resume not found"
        }), 404


    # ==========================================================
    # SAFE JSON LOADER
    # ==========================================================

    def load_json(value, default):

        if not value:
            return default

        try:
            return json.loads(value)

        except (TypeError, json.JSONDecodeError):

            return default


    # ==========================================================
    # LOAD ALL RESUME SECTIONS
    # ==========================================================

    personal = load_json(
        resume_row["personal_info"],
        {}
    )

    education = load_json(
        resume_row["education"],
        []
    )

    skills = load_json(
        resume_row["skills"],
        {}
    )

    projects = load_json(
        resume_row["projects"],
        []
    )

    experience = load_json(
        resume_row["experience"],
        []
    )

    certifications = load_json(
        resume_row["certifications"],
        []
    )

    additional_sections = load_json(
        resume_row["custom_sections"],
        []
    )


    # ==========================================================
    # RETURN COMPLETE RESUME STATE
    # ==========================================================

    return jsonify({

        "success": True,

        "resume": {

            "title":
                resume_row["title"] or "Untitled Resume",

            "personal":
                personal,

            "summary":
                resume_row["summary"] or "",

            "education":
                education,

            "skills":
                skills,

            "projects":
                projects,

            "experience":
                experience,

            "certifications":
                certifications,

            "additionalSections":
                additional_sections,

            "completion":
                resume_row["completion"] or 0,

            "updated_at":
                resume_row["updated_at"]

        }

    })