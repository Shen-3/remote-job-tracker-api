from __future__ import annotations

from fastapi.testclient import TestClient

from jobtracker.main import create_app


def make_client(tmp_path):
    return TestClient(create_app(str(tmp_path / "test.sqlite3")))


def payload(company: str = "T-Bank", direction: str = "qa_automation") -> dict:
    return {
        "company": company,
        "role": "QA Automation Intern",
        "direction": direction,
        "status": "planned",
        "link": "https://example.com/internship",
        "salary": "paid internship",
        "hours_per_week": 30,
        "deadline": "2026-06-15",
        "notes": "Confirm remote format.",
    }


def test_health(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_get_application(tmp_path):
    client = make_client(tmp_path)
    created = client.post("/applications", json=payload()).json()
    assert created["id"] == 1
    assert created["company"] == "T-Bank"

    response = client.get(f"/applications/{created['id']}")
    assert response.status_code == 200
    assert response.json()["role"] == "QA Automation Intern"


def test_filter_by_status_and_direction(tmp_path):
    client = make_client(tmp_path)
    client.post("/applications", json=payload("T-Bank", "qa_automation"))
    client.post("/applications", json=payload("Yandex", "python_backend"))

    qa_items = client.get("/applications?direction=qa_automation").json()
    assert len(qa_items) == 1
    assert qa_items[0]["company"] == "T-Bank"

    planned_items = client.get("/applications?status=planned").json()
    assert len(planned_items) == 2


def test_update_application_status(tmp_path):
    client = make_client(tmp_path)
    created = client.post("/applications", json=payload()).json()

    response = client.patch(
        f"/applications/{created['id']}",
        json={"status": "test_task", "notes": "Test task due Friday."},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "test_task"
    assert "Friday" in response.json()["notes"]


def test_delete_application(tmp_path):
    client = make_client(tmp_path)
    created = client.post("/applications", json=payload()).json()

    assert client.delete(f"/applications/{created['id']}").status_code == 204
    assert client.get(f"/applications/{created['id']}").status_code == 404


def test_summary_counts(tmp_path):
    client = make_client(tmp_path)
    client.post("/applications", json=payload("T-Bank", "qa_automation"))
    client.post("/applications", json=payload("Yandex", "python_backend"))

    summary = client.get("/stats/summary").json()
    assert summary["total"] == 2
    assert summary["by_status"]["planned"] == 2
    assert summary["by_direction"]["qa_automation"] == 1
