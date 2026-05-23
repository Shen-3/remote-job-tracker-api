from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "job_tracker.sqlite3"

APPLICATION_MIGRATIONS = {
    "user_id": "ALTER TABLE applications ADD COLUMN user_id INTEGER REFERENCES users(id)",
    "priority": "ALTER TABLE applications ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'",
    "source": "ALTER TABLE applications ADD COLUMN source TEXT NOT NULL DEFAULT 'direct'",
    "next_action_at": "ALTER TABLE applications ADD COLUMN next_action_at TEXT",
}


def database_path() -> str:
    return os.getenv("JOBTRACKER_DB", str(DEFAULT_DB_PATH))


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or database_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            direction TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            source TEXT NOT NULL DEFAULT 'direct',
            link TEXT,
            salary TEXT,
            hours_per_week INTEGER,
            deadline TEXT,
            next_action_at TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(applications)").fetchall()
    }
    for column_name, migration_sql in APPLICATION_MIGRATIONS.items():
        if column_name not in existing_columns:
            conn.execute(migration_sql)
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)
