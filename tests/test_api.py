from __future__ import annotations

from fastapi.testclient import TestClient

from jobtracker.main import create_app


def make_client(tmp_path):
    return TestClient(create_app(str(tmp_path / "test.sqlite3")))


def auth_headers(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "strong-password",
) -> dict[str, str]:
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def payload(
    company: str = "T-Bank",
    direction: str = "qa_automation",
    priority: str = "medium",
    source: str = "direct",
    next_action_at: str | None = None,
    status: str = "planned",
) -> dict:
    return {
        "company": company,
        "role": "QA Automation Intern",
        "direction": direction,
        "status": status,
        "priority": priority,
        "source": source,
        "link": "https://example.com/internship",
        "salary": "paid internship",
        "hours_per_week": 30,
        "deadline": "2026-06-15",
        "next_action_at": next_action_at,
        "notes": "Confirm remote format.",
    }


def test_health(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}


def test_auth_register_login_and_me(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)

    duplicate = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "strong-password"},
    )
    me = client.get("/me", headers=headers)

    assert duplicate.status_code == 409
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_anonymous_users_cannot_read_applications(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/applications")

    assert response.status_code == 401


def test_create_and_get_application(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    created = client.post("/applications", json=payload(), headers=headers).json()
    assert created["id"] == 1
    assert created["company"] == "T-Bank"
    assert created["priority"] == "medium"
    assert created["source"] == "direct"

    response = client.get(f"/applications/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == "QA Automation Intern"


def test_user_cannot_access_another_users_applications(tmp_path):
    client = make_client(tmp_path)
    user_a_headers = auth_headers(client, email="a@example.com")
    user_b_headers = auth_headers(client, email="b@example.com")
    created = client.post("/applications", json=payload(), headers=user_a_headers).json()

    assert client.get("/applications", headers=user_b_headers).json() == []
    assert client.get(f"/applications/{created['id']}", headers=user_b_headers).status_code == 404
    assert (
        client.patch(
            f"/applications/{created['id']}",
            json={"notes": "Trying to update another user item."},
            headers=user_b_headers,
        ).status_code
        == 404
    )
    assert client.delete(f"/applications/{created['id']}", headers=user_b_headers).status_code == 404


def test_filter_by_status_direction_priority_and_source(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    client.post(
        "/applications",
        json=payload("T-Bank", "qa_automation", priority="high", source="tbank"),
        headers=headers,
    )
    client.post(
        "/applications",
        json=payload("Yandex", "python_backend", priority="low", source="yandex"),
        headers=headers,
    )

    qa_items = client.get("/applications?direction=qa_automation", headers=headers).json()
    assert len(qa_items) == 1
    assert qa_items[0]["company"] == "T-Bank"

    planned_items = client.get("/applications?status=planned", headers=headers).json()
    assert len(planned_items) == 2

    high_priority_items = client.get("/applications?priority=high", headers=headers).json()
    assert len(high_priority_items) == 1
    assert high_priority_items[0]["company"] == "T-Bank"

    yandex_items = client.get("/applications?source=yandex", headers=headers).json()
    assert len(yandex_items) == 1
    assert yandex_items[0]["company"] == "Yandex"


def test_update_application_status(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    created = client.post("/applications", json=payload(), headers=headers).json()

    applied = client.patch(
        f"/applications/{created['id']}",
        json={"status": "applied"},
        headers=headers,
    )
    recruiter_reply = client.patch(
        f"/applications/{created['id']}",
        json={"status": "recruiter_reply"},
        headers=headers,
    )
    response = client.patch(
        f"/applications/{created['id']}",
        json={"status": "test_task", "notes": "Test task due Friday."},
        headers=headers,
    )

    assert applied.status_code == 200
    assert recruiter_reply.status_code == 200
    assert response.status_code == 200
    assert response.json()["status"] == "test_task"
    assert "Friday" in response.json()["notes"]


def test_invalid_status_transition_returns_400(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    created = client.post("/applications", json=payload(), headers=headers).json()

    response = client.patch(f"/applications/{created['id']}", json={"status": "offer"}, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid status transition: planned -> offer"


def test_invalid_dates_return_422(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    invalid_payload = payload()
    invalid_payload["deadline"] = "2026/06/15"
    invalid_payload["next_action_at"] = "15-06-2026"

    response = client.post("/applications", json=invalid_payload, headers=headers)

    assert response.status_code == 422


def test_follow_ups_return_due_active_applications(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    client.post("/applications", json=payload("Due Corp", next_action_at="2000-01-01"), headers=headers)
    client.post(
        "/applications",
        json=payload("Future Corp", next_action_at="2999-01-01"),
        headers=headers,
    )
    client.post(
        "/applications",
        json=payload("Rejected Corp", next_action_at="2000-01-02", status="rejected"),
        headers=headers,
    )

    response = client.get("/applications/follow-ups", headers=headers)

    assert response.status_code == 200
    assert [item["company"] for item in response.json()] == ["Due Corp"]


def test_delete_application(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    created = client.post("/applications", json=payload(), headers=headers).json()

    assert client.delete(f"/applications/{created['id']}", headers=headers).status_code == 204
    assert client.get(f"/applications/{created['id']}", headers=headers).status_code == 404


def test_summary_counts(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    client.post("/applications", json=payload("T-Bank", "qa_automation"), headers=headers)
    client.post("/applications", json=payload("Yandex", "python_backend"), headers=headers)

    summary = client.get("/stats/summary", headers=headers).json()
    assert summary["total"] == 2
    assert summary["by_status"]["planned"] == 2
    assert summary["by_direction"]["qa_automation"] == 1


def test_funnel_weekly_and_source_stats(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    client.post("/applications", json=payload("Applied", status="applied", source="hh"), headers=headers)
    client.post(
        "/applications",
        json=payload("Reply", status="recruiter_reply", source="hh"),
        headers=headers,
    )
    client.post(
        "/applications",
        json=payload("Task", status="test_task", source="tbank"),
        headers=headers,
    )
    client.post(
        "/applications",
        json=payload("Interview", status="interview", source="tbank"),
        headers=headers,
    )
    client.post("/applications", json=payload("Offer", status="offer", source="yandex"), headers=headers)
    client.post("/applications", json=payload("Planned", status="planned", source="direct"), headers=headers)

    funnel = client.get("/stats/funnel", headers=headers).json()
    weekly = client.get("/stats/weekly", headers=headers).json()
    sources = {item["source"]: item for item in client.get("/stats/sources", headers=headers).json()}

    assert funnel["applied"] == 5
    assert funnel["replies"] == 4
    assert funnel["test_tasks"] == 3
    assert funnel["interviews"] == 2
    assert funnel["offers"] == 1
    assert funnel["reply_rate"] == 0.8
    assert weekly[0]["created"] == 6
    assert sources["hh"]["response_rate"] == 0.5
    assert sources["tbank"]["response_rate"] == 1.0


def test_csv_import_export_and_duplicates(tmp_path):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    csv_text = (
        "company,role,direction,status,priority,source,link,salary,hours_per_week,"
        "deadline,next_action_at,notes\n"
        "CSV Corp,Backend Intern,python_backend,planned,high,habr,"
        "https://example.com/csv,paid,20,2026-07-01,2026-07-05,Imported row\n"
        "Bad Corp,QA,unknown_direction,planned,high,habr,"
        "https://example.com/bad,paid,20,2026-07-01,2026-07-05,Bad row\n"
    )

    first_import = client.post(
        "/imports/applications.csv",
        headers=headers,
        files={"file": ("applications.csv", csv_text, "text/csv")},
    )
    second_import = client.post(
        "/imports/applications.csv",
        headers=headers,
        files={"file": ("applications.csv", csv_text, "text/csv")},
    )
    exported = client.get("/exports/applications.csv", headers=headers)

    assert first_import.status_code == 200
    assert first_import.json()["imported"] == 1
    assert first_import.json()["errors"][0]["row"] == 3
    assert second_import.json()["skipped_duplicates"] == 1
    assert exported.status_code == 200
    assert "CSV Corp" in exported.text
