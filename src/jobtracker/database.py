from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "job_tracker.sqlite3"


def database_path() -> str:
    return os.getenv("JOBTRACKER_DB", str(DEFAULT_DB_PATH))


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or database_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            direction TEXT NOT NULL,
            status TEXT NOT NULL,
            link TEXT,
            salary TEXT,
            hours_per_week INTEGER,
            deadline TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)
