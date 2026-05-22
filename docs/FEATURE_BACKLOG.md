# Feature Backlog

These tasks are written so they can be copied into GitHub Issues.

## Priority 1: Make the API Less CRUD-Like

### Add status transition validation

Why: real hiring workflows have rules, and this shows domain modeling.

Implementation:

- Create `workflow.py`.
- Define allowed transitions as a dictionary.
- Validate transitions in `PATCH /applications/{id}`.
- Return `400` with a clear error for invalid transitions.

Acceptance criteria:

- `planned -> applied` works.
- `planned -> offer` fails.
- Tests cover valid and invalid transitions.

### Add follow-up dates

Why: makes the app useful in a real job search.

Implementation:

- Add `next_action_at` field.
- Add filter `due_follow_up=true`.
- Add endpoint `/applications/follow-ups`.

Acceptance criteria:

- Applications with due follow-up dates are returned first.
- Past dates are included, future dates are excluded.

### Add source and priority fields

Why: lets the project support analytics by channel.

Implementation:

- Add enum-like validation for `source`.
- Add enum-like validation for `priority`.
- Extend list filters.

Acceptance criteria:

- Filtering by `source=hh` works.
- Filtering by `priority=high` works.

## Priority 2: Add Auth

### Add user registration and login

Implementation:

- Add `users` table.
- Add password hashing.
- Add `/auth/register`.
- Add `/auth/login`.
- Return JWT access token.

Acceptance criteria:

- Duplicate email returns `409`.
- Wrong password returns `401`.
- Valid login returns token.

### Scope applications by user

Implementation:

- Add `user_id` to applications.
- Use current user in repository functions.
- Never return another user's data.

Acceptance criteria:

- User A list endpoint does not show User B data.
- Cross-user get/update/delete returns `404`.

## Priority 3: Analytics

### Add funnel endpoint

Implementation:

- Add `/stats/funnel`.
- Count applications by meaningful funnel stage.
- Return both counts and rates.

Acceptance criteria:

- Response includes `reply_rate`, `test_task_rate`, `interview_rate`, `offer_rate`.
- Tests verify exact rates on seeded data.

### Add weekly activity endpoint

Implementation:

- Add `/stats/weekly`.
- Group applications by ISO week.
- Return created count and status changes.

Acceptance criteria:

- Endpoint handles empty data.
- Endpoint returns sorted weeks.

## Priority 4: Import and Export

### Add CSV export

Implementation:

- Add `/exports/applications.csv`.
- Include all fields.
- Use `text/csv` response.

Acceptance criteria:

- CSV has header row.
- CSV contains all applications for current user.

### Add CSV import

Implementation:

- Add `/imports/applications.csv`.
- Validate rows before insert.
- Return import summary.

Acceptance criteria:

- Valid rows are inserted.
- Invalid rows are reported with row numbers.
- Duplicate rows are skipped.

## Priority 5: Professional Polish

### Add Docker Compose with PostgreSQL

Implementation:

- Add `docker-compose.yml`.
- Add `DATABASE_URL`.
- Keep SQLite as local fallback.

Acceptance criteria:

- `docker compose up` starts the API.
- Swagger works against Postgres.

### Add GitHub Actions lint step

Implementation:

- Add Ruff.
- Run `ruff check .` in CI.

Acceptance criteria:

- CI runs tests and lint.
- README shows local lint command.
