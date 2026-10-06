from __future__ import annotations

import json
from typing import Any

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database.database import get_db_connection
from utils.resume_parser import parse_resume
from ats.pipeline import ATSAnalysisPipeline
from ats.ai.rewriter import ATSRewriter
from ats.ai.validator import validate_rewrite

analyzer = Blueprint("analyzer", __name__)


def login_required():
    return "user_id" in session


def _load_json(value: Any, default: Any):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _resume_state(row) -> dict[str, Any]:
    return {
        "title": row["title"] or "Untitled Resume",
        "personal": _load_json(row["personal_info"], {}),
        "summary": row["summary"] or "",
        "education": _load_json(row["education"], []),
        "skills": _load_json(row["skills"], {}),
        "projects": _load_json(row["projects"], []),
        "experience": _load_json(row["experience"], []),
        "certifications": _load_json(row["certifications"], []),
        "additionalSections": _load_json(row["custom_sections"], []),
    }


def _resume_to_text(state: dict[str, Any]) -> str:
    """Build analysis text from the current saved Resume Studio state.

    This intentionally uses the database-backed structured state instead of
    stale uploaded extracted_text, so a later Analyze Resume sees saved edits.
    """
    lines: list[str] = []

    personal = state.get("personal") or {}
    for key in ("fullName", "headline", "email", "phone", "location", "linkedin", "github", "portfolio"):
        value = personal.get(key)
        if value:
            lines.append(str(value))

    sections = [
        ("SUMMARY", state.get("summary")),
        ("EDUCATION", state.get("education")),
        ("SKILLS", state.get("skills")),
        ("PROJECTS", state.get("projects")),
        ("EXPERIENCE", state.get("experience")),
        ("CERTIFICATIONS", state.get("certifications")),
    ]

    for heading, value in sections:
        if not value:
            continue
        lines.append(heading)
        if isinstance(value, str):
            lines.append(value)
            continue
        if isinstance(value, dict):
            for key, item in value.items():
                if not item:
                    continue
                if isinstance(item, list):
                    if item:
                        lines.append(f"{key}: {', '.join(map(str, item))}")
                else:
                    lines.append(f"{key}: {item}")
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    lines.append(item)
                    continue
                if not isinstance(item, dict):
                    lines.append(str(item))
                    continue
                title = item.get("title") or item.get("name") or item.get("degree")
                if title:
                    lines.append(str(title))
                for key in ("technologies", "skills"):
                    vals = item.get(key)
                    if isinstance(vals, list) and vals:
                        lines.append(f"{key}: {', '.join(map(str, vals))}")
                bullets = item.get("bullets")
                if isinstance(bullets, list):
                    lines.extend(str(b) for b in bullets if b)
                elif bullets:
                    lines.append(str(bullets))
                responsibilities = item.get("responsibilities")
                if isinstance(responsibilities, list):
                    lines.extend(str(b) for b in responsibilities if b)
                elif responsibilities:
                    lines.append(str(responsibilities))
                description = item.get("description")
                if isinstance(description, list):
                    lines.extend(str(b) for b in description if b)
                elif description:
                    lines.append(str(description))
                for key in ("organization", "institution", "company", "role", "position", "location", "startYear", "endYear", "year"):
                    item_value = item.get(key)
                    if item_value:
                        lines.append(str(item_value))

    for section in state.get("additionalSections") or []:
        if not isinstance(section, dict):
            lines.append(str(section))
            continue
        title = section.get("title") or section.get("name")
        if title:
            lines.append(str(title))
        content = section.get("content") or section.get("description") or section.get("items")
        if isinstance(content, list):
            lines.extend(str(x) for x in content if x)
        elif content:
            lines.append(str(content))

    return "\n".join(lines).strip()


def _normalize_job_description(value: str) -> str:
    """Normalize JD text only for exact-history matching.

    The saved JD itself is never modified; this is only a lookup key so
    harmless whitespace differences do not create duplicate analyses.
    """
    return " ".join((value or "").split()).strip().casefold()


def _get_owned_resume(resume_id: int):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM resumes WHERE id=? AND user_id=?",
        (resume_id, session["user_id"]),
    ).fetchone()
    return conn, row


@analyzer.route("/analyzer")
def analyzer_page():
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    resumes = conn.execute(
        "SELECT id, title FROM resumes WHERE user_id=? ORDER BY updated_at DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    return render_template(
        "analyzer/resume_analyzer.html",
        page_title="ATS Analyzer",
        user_name=session.get("user_name", ""),
        resumes=resumes,
    )


@analyzer.route("/insights")
def insights_page():
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    analyses = conn.execute("""
        SELECT
            id,
            resume_id,
            resume_title,
            job_title,
            score,
            created_at,
            analysis_number
        FROM ats_analyses
        WHERE user_id=?
        ORDER BY created_at DESC, id DESC
    """, (session["user_id"],)).fetchall()

    stats = conn.execute("""
        SELECT
            COUNT(*) AS total_analyses,
            COUNT(DISTINCT resume_id) AS resumes_analyzed,
            AVG(score) AS average_score
        FROM ats_analyses
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    conn.close()

    total_analyses = stats["total_analyses"] or 0
    resumes_analyzed = stats["resumes_analyzed"] or 0
    average_score = round(stats["average_score"], 1) if stats["average_score"] is not None else 0

    return render_template(
        "insights.html",
        page_title="Insights",
        user_name=session.get("user_name", ""),
        analyses=analyses,
        total_analyses=total_analyses,
        resumes_analyzed=resumes_analyzed,
        average_score=average_score,
    )


@analyzer.route("/api/analyzer/analyze", methods=["POST"])
def analyze_resume():
    if not login_required():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    try:
        resume_id = int(data.get("resume_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid resume selected."}), 400

    job_description = (data.get("job_description") or "").strip()
    if not job_description:
        return jsonify({"success": False, "message": "Job description is required."}), 400

    conn, row = _get_owned_resume(resume_id)
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Resume not found."}), 404

    state = _resume_state(row)
    resume_text = _resume_to_text(state)
    conn.close()

    if not resume_text:
        return jsonify({"success": False, "message": "Your resume has no saved content to analyze."}), 400

    # Every explicit Analyze action creates an immutable history snapshot.
    # This ensures a changed Resume Studio state is re-analyzed even when the
    # same job description is submitted again.
    try:
        pipeline = ATSAnalysisPipeline(resume_parser=parse_resume)
        analysis = pipeline.analyze(
            resume_text=resume_text,
            job_description_text=job_description,
            resume_title=state["title"],
        )

        score = float((analysis.get("score") or {}).get("score", 0))
        job_title = (analysis.get("job_description") or {}).get("title", "")

        conn = get_db_connection()
        cursor = conn.cursor()

        next_analysis_number = cursor.execute("""
            SELECT COALESCE(MAX(analysis_number), 0) + 1
            FROM ats_analyses
            WHERE user_id=?
        """, (session["user_id"],)).fetchone()[0]

        cursor.execute("""
            INSERT INTO ats_analyses(
                user_id, resume_id, resume_title, job_title,
                job_description, score, analysis_json, analysis_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            resume_id,
            state["title"],
            job_title,
            job_description,
            score,
            json.dumps(analysis, ensure_ascii=False),
            next_analysis_number,
        ))
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "resume_id": resume_id,
            "job_description": job_description,
            "analysis": analysis,
            "reused": False,
        })

    except Exception as error:
        print("ATS analysis error:", error)
        return jsonify({
            "success": False,
            "message": str(error) or "ATS analysis failed.",
        }), 500


@analyzer.route("/api/analyzer/latest")
def latest_analysis():
    if not login_required():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        resume_id = int(request.args.get("resume_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid resume selected."}), 400

    job_description = (request.args.get("job_description") or "").strip()
    if not job_description:
        # Never return an arbitrary historical JD just because a resume was selected.
        return jsonify({"success": True, "analysis": None})

    target = _normalize_job_description(job_description)

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, resume_id, resume_title, job_title, job_description,
               score, analysis_json, created_at
        FROM ats_analyses
        WHERE user_id=? AND resume_id=?
        ORDER BY created_at DESC, id DESC
    """, (session["user_id"], resume_id)).fetchall()
    conn.close()

    for row in rows:
        if _normalize_job_description(row["job_description"]) != target:
            continue

        return jsonify({
            "success": True,
            "analysis_id": row["id"],
            "resume_id": row["resume_id"],
            "job_description": row["job_description"],
            "created_at": row["created_at"],
            "analysis": json.loads(row["analysis_json"]),
        })

    return jsonify({"success": True, "analysis": None})


@analyzer.route("/api/analyzer/analysis/<int:analysis_id>")
def get_analysis(analysis_id: int):
    if not login_required():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db_connection()
    row = conn.execute("""
        SELECT id, resume_id, resume_title, job_title, job_description,
               score, analysis_json, created_at
        FROM ats_analyses
        WHERE id=? AND user_id=?
    """, (analysis_id, session["user_id"])).fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "Analysis not found."}), 404

    return jsonify({
        "success": True,
        "analysis_id": row["id"],
        "resume_id": row["resume_id"],
        "job_description": row["job_description"],
        "created_at": row["created_at"],
        "analysis": json.loads(row["analysis_json"]),
    })


@analyzer.route("/api/analyzer/analysis/<int:analysis_id>/delete", methods=["DELETE", "POST"])
def delete_analysis(analysis_id: int):
    if not login_required():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db_connection()
    row = conn.execute("""
        SELECT id
        FROM ats_analyses
        WHERE id=? AND user_id=?
    """, (analysis_id, session["user_id"])).fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Analysis not found."}), 404

    conn.execute("""
        DELETE FROM ats_analyses
        WHERE id=? AND user_id=?
    """, (analysis_id, session["user_id"]))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "analysis_id": analysis_id})


@analyzer.route("/api/analyzer/rewrite", methods=["POST"])
def rewrite_resume_content():
    if not login_required():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    job_description = (data.get("job_description") or "").strip()
    content_type = data.get("content_type") or "bullet"
    resume_id = data.get("resume_id")

    if not content or not job_description:
        return jsonify({"success": False, "message": "Resume content and job description are required."}), 400

    try:
        resume_id = int(resume_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid resume selected."}), 400

    conn, row = _get_owned_resume(resume_id)
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Resume not found."}), 404

    state = _resume_state(row)
    conn.close()

    try:
        from ats.jd_parser import parse_job_description
        jd = parse_job_description(job_description)
        rewriter = ATSRewriter()

        if content_type == "summary":
            rewrite = rewriter.rewrite_summary(
                summary=content,
                job_description=jd,
                resume_context=state,
            )
        else:
            rewrite = rewriter.rewrite_bullet(
                bullet=content,
                job_description=jd,
                resume_context=state,
            )

        validation = validate_rewrite(
            original=rewrite["original"],
            rewritten=rewrite["rewritten"],
            resume_context=state,
        )

        return jsonify({"success": True, "rewrite": rewrite, "validation": validation})

    except Exception as error:
        print("ATS rewrite error:", error)
        return jsonify({"success": False, "message": str(error) or "AI rewrite failed."}), 500


@analyzer.route("/api/analyzer/apply-rewrite", methods=["POST"])
def apply_rewrite():
    if not login_required():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    try:
        resume_id = int(data.get("resume_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid resume selected."}), 400

    content_type = data.get("content_type") or "bullet"
    section_type = data.get("section_type") or ""
    section_index = data.get("section_index", -1)
    bullet_index = data.get("bullet_index", -1)
    new_content = (data.get("content") or "").strip()
    original_content = data.get("original_content")

    if not new_content:
        return jsonify({"success": False, "message": "Updated content cannot be empty."}), 400

    try:
        section_index = int(section_index)
        bullet_index = int(bullet_index)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid content location."}), 400

    conn, row = _get_owned_resume(resume_id)
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Resume not found."}), 404

    state = _resume_state(row)

    if content_type == "summary":
        state["summary"] = new_content
    else:
        collection_name = section_type if section_type in {"projects", "experience"} else None
        if collection_name is None:
            conn.close()
            return jsonify({"success": False, "message": "Unsupported resume section."}), 400

        collection = state.get(collection_name) or []
        if not (0 <= section_index < len(collection)):
            conn.close()
            return jsonify({"success": False, "message": "Resume section not found."}), 404

        entry = collection[section_index]
        bullets_key = None
        for candidate in ("bullets", "responsibilities", "description"):
            if candidate in entry:
                bullets_key = candidate
                break

        if bullets_key is None:
            entry["bullets"] = []
            bullets_key = "bullets"

        bullets = entry.get(bullets_key)
        if isinstance(bullets, list):
            if not (0 <= bullet_index < len(bullets)):
                conn.close()
                return jsonify({"success": False, "message": "Resume bullet not found."}), 404
            if original_content is not None and str(bullets[bullet_index]).strip() != str(original_content).strip():
                conn.close()
                return jsonify({"success": False, "message": "This resume content has changed. Refresh and try again."}), 409
            bullets[bullet_index] = new_content
        elif isinstance(bullets, str):
            if bullet_index not in (-1, 0):
                conn.close()
                return jsonify({"success": False, "message": "Resume content location is invalid."}), 400
            if original_content is not None and bullets.strip() != str(original_content).strip():
                conn.close()
                return jsonify({"success": False, "message": "This resume content has changed. Refresh and try again."}), 409
            entry[bullets_key] = new_content
        else:
            conn.close()
            return jsonify({"success": False, "message": "Resume content format is unsupported."}), 400

    conn.execute("""
        UPDATE resumes
        SET title=?, summary=?, personal_info=?, education=?, skills=?,
            projects=?, experience=?, certifications=?, custom_sections=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=? AND user_id=?
    """, (
        state["title"],
        state["summary"],
        json.dumps(state["personal"], ensure_ascii=False),
        json.dumps(state["education"], ensure_ascii=False),
        json.dumps(state["skills"], ensure_ascii=False),
        json.dumps(state["projects"], ensure_ascii=False),
        json.dumps(state["experience"], ensure_ascii=False),
        json.dumps(state["certifications"], ensure_ascii=False),
        json.dumps(state["additionalSections"], ensure_ascii=False),
        resume_id,
        session["user_id"],
    ))
    conn.commit()
    conn.close()

    return jsonify({"success": True})
