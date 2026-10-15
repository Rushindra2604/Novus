
import os
import sqlite3
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQLITE_PATH = PROJECT_ROOT / "database" / "novus_backup.db"

load_dotenv(PROJECT_ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

TABLE_COLUMNS = {
    "users": [
        "id", "full_name", "email", "password", "created_at",
    ],
    "resumes": [
        "id", "user_id", "title", "source_type", "uploaded_filename",
        "extracted_text", "personal_info", "summary", "education",
        "skills", "projects", "experience", "certifications",
        "custom_sections", "completion", "created_at", "updated_at",
        "resume_number",
    ],
    "ats_analyses": [
        "id", "user_id", "resume_id", "resume_title", "job_title",
        "job_description", "score", "analysis_json", "created_at",
        "analysis_number",
    ],
}


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing from .env")

    if not SQLITE_PATH.is_file() or SQLITE_PATH.stat().st_size == 0:
        raise RuntimeError(f"SQLite backup is missing or empty: {SQLITE_PATH}")

    # Read the SQLite backup without modifying it.
    with sqlite3.connect(f"file:{SQLITE_PATH.as_posix()}?mode=ro", uri=True) as source:
        source.row_factory = sqlite3.Row
        records = {
            table: [
                dict(row)
                for row in source.execute(
                    f"SELECT * FROM {table} ORDER BY id"
                ).fetchall()
            ]
            for table in TABLE_COLUMNS
        }

    print("Local backup record counts:")
    for table, rows in records.items():
        print(f"  {table}: {len(rows)}")

    # Abort if Neon already contains records. This avoids accidental duplicates.
    with psycopg.connect(DATABASE_URL, connect_timeout=10) as target:
        with target.cursor() as cursor:
            for table in TABLE_COLUMNS:
                cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table)
                    )
                )
                count = cursor.fetchone()[0]

                if count:
                    raise RuntimeError(
                        f"Neon table '{table}' already contains {count} records. "
                        "Migration stopped without inserting data."
                    )

            # Insert users before resumes, then ATS analyses.
            for table in ("users", "resumes", "ats_analyses"):
                columns = TABLE_COLUMNS[table]
                rows = records[table]

                if not rows:
                    continue

                insert_query = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({})"
                ).format(
                    sql.Identifier(table),
                    sql.SQL(", ").join(
                        sql.Identifier(column) for column in columns
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder() for _ in columns
                    ),
                )

                for row in rows:
                    cursor.execute(
                        insert_query,
                        tuple(row.get(column) for column in columns),
                    )

            # Synchronize PostgreSQL identity sequences with preserved IDs.
            for table in TABLE_COLUMNS:
                query = sql.SQL("""
                    SELECT setval(
                        pg_get_serial_sequence(%s, 'id'),
                        COALESCE((SELECT MAX(id) FROM {table}), 1),
                        EXISTS(SELECT 1 FROM {table})
                    )
                """).format(table=sql.Identifier(table))

                cursor.execute(query, (f"public.{table}",))


            print("\nMigration completed. Inserted record counts:")
            for table in TABLE_COLUMNS:
                cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table)
                    )
                )
                print(f"  {table}: {cursor.fetchone()[0]}")

    print("\nThe SQLite backup was not modified.")


if __name__ == "__main__":
    main()
