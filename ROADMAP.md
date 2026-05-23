# Roadmap

This roadmap turns the project from a clean FastAPI CRUD demo into a stronger portfolio backend that looks closer to a real internal tool.

## Hiring Goal

Show that the project is not a stub:

- it has real workflow logic;
- it has tests beyond happy paths;
- it has persistence, auth, analytics, and export/import features;
- it can be deployed and extended without rewriting the core.

## Current Progress

- Milestone 1 is implemented: workflow transitions, follow-up dates, priority/source fields, filters, and tests.
- Milestone 2 is implemented for local usage: users, password hashing, JWT login, `/me`, and user-scoped applications.
- Milestone 3 is partially implemented: summary, funnel, weekly, and source response-rate endpoints.
- Milestone 4 is partially implemented: CSV export/import with duplicate detection and validation reports.
- Milestone 5 is partially implemented: Docker Compose, database health check, Ruff, and GitHub Actions CI.

## Milestone 1: Strong CRUD and Workflow

Goal: make the application tracker useful for a real job search.

Features:

- Add status transition rules:
  - `planned -> applied`;
  - `applied -> recruiter_reply | rejected`;
  - `recruiter_reply -> test_task | interview | rejected`;
  - `test_task -> interview | rejected`;
  - `interview -> offer | rejected`.
- Add `next_action_at` field for follow-ups.
- Add `priority` field: `low`, `medium`, `high`.
- Add `source` field: `hh`, `habr`, `tbank`, `yandex`, `vk`, `ozon`, `freelance`, `direct`.
- Add validation so deadlines and follow-up dates use ISO date format.

Acceptance criteria:

- Invalid status transitions return `400`.
- Filtering works by `status`, `direction`, `priority`, and `source`.
- Tests cover create, update, invalid transition, and filters.

## Milestone 2: Authentication and User Accounts

Goal: show backend fundamentals expected from junior backend roles.

Features:

- Add users table.
- Add password hashing with `passlib` or `pwdlib`.
- Add JWT login.
- Scope applications by user.
- Add `/me` endpoint.

Acceptance criteria:

- Anonymous users cannot read or change applications.
- User A cannot access User B applications.
- Auth tests cover login, protected route, and cross-user access denial.

## Milestone 3: Analytics Dashboard API

Goal: make the project relevant for data and product analytics roles.

Features:

- Add conversion funnel:
  - applied;
  - replies;
  - test tasks;
  - interviews;
  - offers.
- Add weekly activity summary.
- Add response rate by source.
- Add average days from application to first reply.
- Add endpoint `/stats/funnel`.
- Add endpoint `/stats/weekly`.

Acceptance criteria:

- Analytics endpoints return deterministic JSON.
- Tests seed sample data and assert exact metrics.
- README shows sample analytics output.

## Milestone 4: Import, Export, and Automation

Goal: show practical automation value.

Features:

- CSV export of all applications.
- CSV import with validation report.
- Duplicate detection by company + role + link.
- Follow-up reminder list.
- Optional Telegram notification integration.

Acceptance criteria:

- Exported CSV can be imported back.
- Invalid CSV rows are reported without crashing the whole import.
- Tests cover duplicates and malformed rows.

## Milestone 5: Production Readiness

Goal: make the repository look professional.

Features:

- PostgreSQL support through `DATABASE_URL`.
- Alembic migrations.
- Docker Compose with API + Postgres.
- Structured logging.
- GitHub Actions test workflow with linting.
- Health check includes database connectivity.

Acceptance criteria:

- `docker compose up` starts the API.
- Tests run in GitHub Actions.
- README has local and Docker setup.

## Suggested Demo After Roadmap

1. Register a user.
2. Create applications from different sources.
3. Move one application through statuses.
4. Show invalid transition rejection.
5. Export CSV.
6. Show funnel metrics.
7. Run tests.
