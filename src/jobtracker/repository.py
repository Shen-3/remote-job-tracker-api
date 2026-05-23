from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from jobtracker.database import row_to_dict


CREATE_FIELDS = (
    "company",
    "role",
    "direction",
    "status",
    "priority",
    "source",
    "link",
    "salary",
    "hours_per_week",
    "deadline",
    "next_action_at",
    "notes",
)
EXPORT_FIELDS = ("id", *CREATE_FIELDS, "created_at", "updated_at")
REPLY_STATUSES = ("recruiter_reply", "test_task", "interview", "offer")


def create_user(conn: sqlite3.Connection, email: str, password_hash: str) -> dict[str, Any] | None:
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)",
            {"email": normalize_email(email), "password_hash": password_hash},
        )
    except sqlite3.IntegrityError:
        return None

    conn.commit()
    return get_user_by_id(conn, cursor.lastrowid)


def get_user_by_email(conn: sqlite3.Connection, email: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (normalize_email(email),),
    ).fetchone()
    return row_to_dict(row)


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row)


def create_application(
    conn: sqlite3.Connection,
    user_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    values = {field: payload.get(field) for field in CREATE_FIELDS}
    values["user_id"] = user_id
    cursor = conn.execute(
        """
        INSERT INTO applications (
            user_id, company, role, direction, status, priority, source, link, salary,
            hours_per_week, deadline, next_action_at, notes
        )
        VALUES (
            :user_id, :company, :role, :direction, :status, :priority, :source, :link, :salary,
            :hours_per_week, :deadline, :next_action_at, :notes
        )
        """,
        values,
    )
    conn.commit()
    created = get_application(conn, user_id, cursor.lastrowid)
    if created is None:
        raise RuntimeError("application was not created")
    return created


def list_applications(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    status: str | None = None,
    direction: str | None = None,
    priority: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["user_id = :user_id"]
    params: dict[str, Any] = {"user_id": user_id}
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if direction:
        clauses.append("direction = :direction")
        params["direction"] = direction
    if priority:
        clauses.append("priority = :priority")
        params["priority"] = priority
    if source:
        clauses.append("source = :source")
        params["source"] = source

    rows = conn.execute(
        f"""
        SELECT *
        FROM applications
        WHERE {' AND '.join(clauses)}
        ORDER BY created_at DESC, id DESC
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def get_application(
    conn: sqlite3.Connection,
    user_id: int,
    application_id: int,
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ? AND user_id = ?",
        (application_id, user_id),
    ).fetchone()
    return row_to_dict(row)


def list_follow_ups(
    conn: sqlite3.Connection,
    user_id: int,
    today: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM applications
        WHERE user_id = :user_id
          AND next_action_at IS NOT NULL
          AND next_action_at <= :today
          AND status NOT IN ('offer', 'rejected')
        ORDER BY next_action_at ASC, created_at DESC, id DESC
        """,
        {"user_id": user_id, "today": today},
    ).fetchall()
    return [dict(row) for row in rows]


def update_application(
    conn: sqlite3.Connection,
    user_id: int,
    application_id: int,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    allowed = set(CREATE_FIELDS)
    updates = {key: value for key, value in payload.items() if key in allowed and value is not None}
    if not updates:
        return get_application(conn, user_id, application_id)

    assignments = ", ".join(f"{key} = :{key}" for key in updates)
    updates["id"] = application_id
    updates["user_id"] = user_id
    conn.execute(
        f"""
        UPDATE applications
        SET {assignments}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :id AND user_id = :user_id
        """,
        updates,
    )
    conn.commit()
    return get_application(conn, user_id, application_id)


def delete_application(conn: sqlite3.Connection, user_id: int, application_id: int) -> bool:
    cursor = conn.execute(
        "DELETE FROM applications WHERE id = ? AND user_id = ?",
        (application_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def duplicate_application_exists(
    conn: sqlite3.Connection,
    user_id: int,
    company: str,
    role: str,
    link: str | None,
) -> bool:
    row = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE user_id = :user_id
          AND lower(company) = lower(:company)
          AND lower(role) = lower(:role)
          AND coalesce(link, '') = coalesce(:link, '')
        LIMIT 1
        """,
        {"user_id": user_id, "company": company, "role": role, "link": link},
    ).fetchone()
    return row is not None


def summary(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    total = conn.execute(
        "SELECT COUNT(*) AS count FROM applications WHERE user_id = ?",
        (user_id,),
    ).fetchone()["count"]
    by_status = conn.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM applications
        WHERE user_id = ?
        GROUP BY status
        ORDER BY count DESC
        """,
        (user_id,),
    ).fetchall()
    by_direction = conn.execute(
        """
        SELECT direction, COUNT(*) AS count
        FROM applications
        WHERE user_id = ?
        GROUP BY direction
        ORDER BY count DESC
        """,
        (user_id,),
    ).fetchall()
    return {
        "total": total,
        "by_status": {row["status"]: row["count"] for row in by_status},
        "by_direction": {row["direction"]: row["count"] for row in by_direction},
    }


def funnel(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    counts = _status_counts(conn, user_id)
    applied = sum(counts.get(status, 0) for status in (*REPLY_STATUSES, "applied", "rejected"))
    replies = sum(counts.get(status, 0) for status in REPLY_STATUSES)
    test_tasks = sum(counts.get(status, 0) for status in ("test_task", "interview", "offer"))
    interviews = sum(counts.get(status, 0) for status in ("interview", "offer"))
    offers = counts.get("offer", 0)

    return {
        "applied": applied,
        "replies": replies,
        "test_tasks": test_tasks,
        "interviews": interviews,
        "offers": offers,
        "reply_rate": _rate(replies, applied),
        "test_task_rate": _rate(test_tasks, applied),
        "interview_rate": _rate(interviews, applied),
        "offer_rate": _rate(offers, applied),
        "average_days_to_first_reply": _average_days_to_reply(conn, user_id),
    }


def weekly_activity(conn: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT created_at FROM applications WHERE user_id = ? ORDER BY created_at ASC",
        (user_id,),
    ).fetchall()
    weeks: dict[str, int] = {}
    for row in rows:
        iso_week = datetime.fromisoformat(row["created_at"]).date().isocalendar()
        week_key = f"{iso_week.year}-W{iso_week.week:02d}"
        weeks[week_key] = weeks.get(week_key, 0) + 1
    return [{"week": week, "created": count} for week, count in sorted(weeks.items())]


def response_rate_by_source(conn: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            source,
            COUNT(*) AS total,
            SUM(CASE WHEN status IN ('recruiter_reply', 'test_task', 'interview', 'offer')
                THEN 1 ELSE 0 END) AS replies
        FROM applications
        WHERE user_id = ?
        GROUP BY source
        ORDER BY total DESC, source ASC
        """,
        (user_id,),
    ).fetchall()
    return [
        {
            "source": row["source"],
            "total": row["total"],
            "replies": row["replies"],
            "response_rate": _rate(row["replies"], row["total"]),
        }
        for row in rows
    ]


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _status_counts(conn: sqlite3.Connection, user_id: int) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM applications
        WHERE user_id = ?
        GROUP BY status
        """,
        (user_id,),
    ).fetchall()
    return {row["status"]: row["count"] for row in rows}


def _average_days_to_reply(conn: sqlite3.Connection, user_id: int) -> float | None:
    rows = conn.execute(
        """
        SELECT created_at, updated_at
        FROM applications
        WHERE user_id = ?
          AND status IN ('recruiter_reply', 'test_task', 'interview', 'offer')
        """,
        (user_id,),
    ).fetchall()
    if not rows:
        return None

    total_days = 0.0
    for row in rows:
        created_at = datetime.fromisoformat(row["created_at"])
        updated_at = datetime.fromisoformat(row["updated_at"])
        total_days += (updated_at - created_at).total_seconds() / 86400
    return round(total_days / len(rows), 2)


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 2)
