from __future__ import annotations

import sqlite3
from typing import Any

from jobtracker.database import row_to_dict


CREATE_FIELDS = (
    "company",
    "role",
    "direction",
    "status",
    "link",
    "salary",
    "hours_per_week",
    "deadline",
    "notes",
)


def create_application(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    values = {field: payload.get(field) for field in CREATE_FIELDS}
    cursor = conn.execute(
        """
        INSERT INTO applications (
            company, role, direction, status, link, salary, hours_per_week, deadline, notes
        )
        VALUES (
            :company, :role, :direction, :status, :link, :salary, :hours_per_week, :deadline, :notes
        )
        """,
        values,
    )
    conn.commit()
    created = get_application(conn, cursor.lastrowid)
    if created is None:
        raise RuntimeError("application was not created")
    return created


def list_applications(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    direction: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, str] = {}
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if direction:
        clauses.append("direction = :direction")
        params["direction"] = direction

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM applications {where_sql} ORDER BY created_at DESC, id DESC",
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def get_application(conn: sqlite3.Connection, application_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    return row_to_dict(row)


def update_application(
    conn: sqlite3.Connection,
    application_id: int,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    allowed = set(CREATE_FIELDS)
    updates = {key: value for key, value in payload.items() if key in allowed and value is not None}
    if not updates:
        return get_application(conn, application_id)

    assignments = ", ".join(f"{key} = :{key}" for key in updates)
    updates["id"] = application_id
    conn.execute(
        f"""
        UPDATE applications
        SET {assignments}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :id
        """,
        updates,
    )
    conn.commit()
    return get_application(conn, application_id)


def delete_application(conn: sqlite3.Connection, application_id: int) -> bool:
    cursor = conn.execute("DELETE FROM applications WHERE id = ?", (application_id,))
    conn.commit()
    return cursor.rowcount > 0


def summary(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS count FROM applications").fetchone()["count"]
    by_status = conn.execute(
        "SELECT status, COUNT(*) AS count FROM applications GROUP BY status ORDER BY count DESC"
    ).fetchall()
    by_direction = conn.execute(
        "SELECT direction, COUNT(*) AS count FROM applications GROUP BY direction ORDER BY count DESC"
    ).fetchall()
    return {
        "total": total,
        "by_status": {row["status"]: row["count"] for row in by_status},
        "by_direction": {row["direction"]: row["count"] for row in by_direction},
    }
