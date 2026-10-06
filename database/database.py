import sqlite3

DATABASE = "database/novus.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source_type TEXT DEFAULT 'created',
            uploaded_filename TEXT,
            extracted_text TEXT,
            personal_info TEXT,
            summary TEXT,
            education TEXT,
            skills TEXT,
            projects TEXT,
            experience TEXT,
            certifications TEXT,
            custom_sections TEXT,
            completion INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resume_number INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Safe migrations for existing Novus databases.
    resume_columns = {
        "source_type": "TEXT DEFAULT 'created'",
        "uploaded_filename": "TEXT",
        "extracted_text": "TEXT",
    }

    existing_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(resumes)").fetchall()
    }

    for column_name, column_definition in resume_columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE resumes ADD COLUMN {column_name} {column_definition}"
            )

    # Safe migration for user-facing resume numbering. The database id remains
    # the stable internal primary key and is never renumbered.
    resume_number_exists = cursor.execute(
        "PRAGMA table_info(resumes)"
    ).fetchall()
    resume_column_names = {row["name"] for row in resume_number_exists}
    resume_number_added = False
    if "resume_number" not in resume_column_names:
        cursor.execute("ALTER TABLE resumes ADD COLUMN resume_number INTEGER")
        resume_number_added = True

    # Existing databases may contain large internal IDs from deleted test
    # resumes. Rebuild the user-facing sequence once so the currently saved
    # resumes appear as 1..N. The internal primary key is untouched.
    users_with_resumes = cursor.execute(
        "SELECT DISTINCT user_id FROM resumes"
    ).fetchall()
    for user_row in users_with_resumes:
        user_id = user_row["user_id"]
        needs_backfill = resume_number_added or cursor.execute(
            "SELECT 1 FROM resumes WHERE user_id=? AND resume_number IS NULL LIMIT 1",
            (user_id,),
        ).fetchone()
        if not needs_backfill:
            continue
        rows = cursor.execute("""
            SELECT id
            FROM resumes
            WHERE user_id=?
            ORDER BY created_at ASC, id ASC
        """, (user_id,)).fetchall()
        for position, resume_row in enumerate(rows, start=1):
            cursor.execute(
                "UPDATE resumes SET resume_number=? WHERE id=? AND user_id=?",
                (position, resume_row["id"], user_id),
            )

    # Permanent ATS analysis history. Each row is one immutable analysis snapshot.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ats_analyses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_id INTEGER NOT NULL,
            resume_title TEXT NOT NULL,
            job_title TEXT,
            job_description TEXT NOT NULL,
            score REAL,
            analysis_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analysis_number INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(resume_id) REFERENCES resumes(id)
        )
    """)

    analysis_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(ats_analyses)").fetchall()}
    analysis_number_added = False
    if "analysis_number" not in analysis_columns:
        cursor.execute("ALTER TABLE ats_analyses ADD COLUMN analysis_number INTEGER")
        analysis_number_added = True

    users_with_analyses = cursor.execute(
        "SELECT DISTINCT user_id FROM ats_analyses"
    ).fetchall()
    for user_row in users_with_analyses:
        user_id = user_row["user_id"]
        needs_backfill = analysis_number_added or cursor.execute(
            "SELECT 1 FROM ats_analyses WHERE user_id=? AND analysis_number IS NULL LIMIT 1",
            (user_id,),
        ).fetchone()
        if not needs_backfill:
            continue
        rows = cursor.execute("""
            SELECT id
            FROM ats_analyses
            WHERE user_id=?
            ORDER BY created_at ASC, id ASC
        """, (user_id,)).fetchall()
        for position, analysis_row in enumerate(rows, start=1):
            cursor.execute(
                "UPDATE ats_analyses SET analysis_number=? WHERE id=? AND user_id=?",
                (position, analysis_row["id"], user_id),
            )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ats_analyses_user_created
        ON ats_analyses(user_id, created_at DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ats_analyses_resume_created
        ON ats_analyses(resume_id, created_at DESC)
    """)

    conn.commit()
    conn.close()
