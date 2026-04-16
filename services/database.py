from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "applications.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '',
            job_url TEXT NOT NULL,
            rating INTEGER,
            explanation TEXT,
            tailored_resume TEXT,
            status TEXT NOT NULL DEFAULT 'Applied',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_application(job_title: str, company: str, job_url: str, rating: int,
                     explanation: str, tailored_resume: str) -> int:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO applications (job_title, company, job_url, rating, explanation,
           tailored_resume, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'Applied', ?, ?)""",
        (job_title, company, job_url, rating, explanation, tailored_resume, now, now),
    )
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return app_id


def get_all_applications() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_application(app_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_application_status(app_id: int, status: str, notes: Optional[str] = None) -> bool:
    now = datetime.now().isoformat()
    conn = get_connection()
    if notes is not None:
        conn.execute(
            "UPDATE applications SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
            (status, notes, now, app_id),
        )
    else:
        conn.execute(
            "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, app_id),
        )
    conn.commit()
    conn.close()
    return True


def delete_application(app_id: int) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()
    return True
