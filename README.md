# Remote Job Tracker API

FastAPI backend for tracking remote internship and junior job applications.

This is a portfolio project for Python backend, QA automation, and junior data roles. It shows CRUD API design, SQLite persistence, filtering, validation, tests, and a small analytics endpoint.

## Why this project is useful for hiring

- Shows a real problem: managing many internship/job applications.
- Demonstrates backend basics: REST API, validation, persistence, filtering.
- Gives QA material: endpoints are easy to cover with API tests.
- Gives data material: summary endpoint calculates conversion-style metrics.

## Features

- Create, list, update, and delete applications.
- Filter applications by status and direction.
- Track company, role, link, salary, weekly hours, deadline, and notes.
- Summary endpoint for application counts by status and direction.
- SQLite by default, simple to run locally.
- pytest test suite.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLite
- pytest
- httpx / FastAPI TestClient

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn jobtracker.main:app --reload
```

Open:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

## Run Tests

```bash
pytest
```

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "company": "T-Bank",
    "role": "QA Automation Intern",
    "direction": "qa_automation",
    "status": "planned",
    "link": "https://education.tbank.ru/start/quality_engineer/",
    "salary": "paid internship",
    "hours_per_week": 30,
    "deadline": "2026-06-15",
    "notes": "Remote format and 20-30h/week should be confirmed."
  }'
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | health check |
| POST | `/applications` | create application |
| GET | `/applications` | list applications |
| GET | `/applications/{id}` | get one application |
| PATCH | `/applications/{id}` | update application |
| DELETE | `/applications/{id}` | delete application |
| GET | `/stats/summary` | counts by status and direction |

## Project Growth

- [Roadmap](ROADMAP.md) - staged feature plan for making the API production-like.
- [Feature backlog](docs/FEATURE_BACKLOG.md) - issue-ready tasks with acceptance criteria.

## Portfolio Demo Script

1. Start the API.
2. Open Swagger.
3. Create 3 applications in different directions.
4. Change one status to `test_task`.
5. Filter by `status=test_task`.
6. Open `/stats/summary`.
7. Run `pytest`.

## Russian Summary

Проект показывает базовый backend-уровень: FastAPI, REST, SQLite, валидация, фильтры и тесты. Его удобно показывать на собеседованиях на Python backend, QA automation и data analyst intern/junior роли.
