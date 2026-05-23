# Remote Job Tracker API

FastAPI backend for tracking remote internship and junior job applications.

This is a portfolio project for Python backend, QA automation, and junior data roles. It shows CRUD API design, JWT auth, SQLite persistence, filtering, workflow validation, follow-up tracking, CSV automation, tests, and analytics endpoints.

## Why this project is useful for hiring

- Shows a real problem: managing many internship/job applications.
- Demonstrates backend basics: REST API, auth, validation, persistence, filtering.
- Gives QA material: endpoints are easy to cover with API tests.
- Gives data material: stats endpoints calculate conversion-style metrics.

## Features

- Create, list, update, and delete applications.
- Register users, login with JWT, and scope applications by account.
- Enforce realistic status transitions for the hiring workflow.
- Filter applications by status, direction, priority, and source.
- Track company, role, source, priority, link, salary, weekly hours, deadline, follow-up date, and notes.
- List due follow-ups for active applications.
- Summary, funnel, weekly activity, and source response-rate analytics.
- CSV import/export with duplicate detection and row-level validation errors.
- Ruff linting and GitHub Actions CI.
- SQLite by default, simple to run locally.
- pytest test suite.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLite
- pwdlib / Argon2 password hashing
- PyJWT
- pytest
- Ruff
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
ruff check .
```

## Docker

```bash
docker compose up --build
```

## Example Requests

Register and login:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "strong-password"}'

curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "strong-password"}'
```

Create an application with the returned bearer token:

```bash
curl -X POST http://127.0.0.1:8000/applications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "company": "T-Bank",
    "role": "QA Automation Intern",
    "direction": "qa_automation",
    "status": "planned",
    "priority": "high",
    "source": "tbank",
    "link": "https://education.tbank.ru/start/quality_engineer/",
    "salary": "paid internship",
    "hours_per_week": 30,
    "deadline": "2026-06-15",
    "next_action_at": "2026-06-20",
    "notes": "Remote format and 20-30h/week should be confirmed."
  }'
```

Valid status transitions:

| From | To |
|---|---|
| `planned` | `applied` |
| `applied` | `recruiter_reply`, `rejected` |
| `recruiter_reply` | `test_task`, `interview`, `rejected` |
| `test_task` | `interview`, `rejected` |
| `interview` | `offer`, `rejected` |

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | health check with database connectivity |
| POST | `/auth/register` | register user |
| POST | `/auth/login` | login and receive JWT |
| GET | `/me` | current user profile |
| POST | `/applications` | create application |
| GET | `/applications` | list applications |
| GET | `/applications/{id}` | get one application |
| PATCH | `/applications/{id}` | update application |
| DELETE | `/applications/{id}` | delete application |
| GET | `/applications/follow-ups` | list due follow-ups |
| GET | `/stats/summary` | counts by status and direction |
| GET | `/stats/funnel` | conversion-style funnel metrics |
| GET | `/stats/weekly` | weekly created applications |
| GET | `/stats/sources` | response rate by source |
| GET | `/exports/applications.csv` | export applications to CSV |
| POST | `/imports/applications.csv` | import applications from CSV |

## Project Growth

- [Roadmap](ROADMAP.md) - staged feature plan for making the API production-like.
- [Feature backlog](docs/FEATURE_BACKLOG.md) - issue-ready tasks with acceptance criteria.

## Portfolio Demo Script

1. Start the API.
2. Open Swagger.
3. Register two users and show that each sees only their own applications.
4. Create 3 applications in different directions.
5. Move one application from `planned` to `applied`, then to `recruiter_reply`.
6. Try `planned -> offer` and show the `400` validation error.
7. Filter by `priority=high` and `source=tbank`.
8. Import/export CSV and show duplicate rows are skipped.
9. Open `/applications/follow-ups`, `/stats/funnel`, `/stats/weekly`, and `/stats/sources`.
10. Run `pytest` and `ruff check .`.

## Russian Summary

Проект показывает backend-уровень ближе к реальному внутреннему сервису: FastAPI, REST, JWT auth, SQLite, валидация, фильтры, workflow-правила, CSV-автоматизация, аналитика, Docker и CI. Его удобно показывать на собеседованиях на Python backend, QA automation и data analyst intern/junior роли.
