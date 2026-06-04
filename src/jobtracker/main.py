from __future__ import annotations

import csv
from collections.abc import Generator
from datetime import date
from io import StringIO
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Response, UploadFile, status
from pydantic import ValidationError

from jobtracker import repository
from jobtracker.database import connect, init_db
from jobtracker.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    CsvImportReport,
    Direction,
    Priority,
    Source,
    Status,
    TokenRead,
    UserLogin,
    UserRead,
    UserRegister,
)
from jobtracker.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from jobtracker.workflow import is_valid_status_transition, status_transition_error


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Remote Job Tracker API",
        version="0.2.0",
        description="Track remote internship and junior job applications.",
    )

    def get_db() -> Generator:
        conn = connect(db_path)
        init_db(conn)
        try:
            yield conn
        finally:
            conn.close()

    def get_current_user(
        authorization: str | None = Header(default=None),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        token = _bearer_token(authorization)
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")

        user_id = decode_access_token(token)
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

        user = repository.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
        return user

    @app.get("/health")
    def health(db=Depends(get_db)) -> dict[str, str]:
        db.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "ok"}

    @app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
    def register(payload: UserRegister, db=Depends(get_db)) -> dict[str, Any]:
        user = repository.create_user(db, payload.email, hash_password(payload.password))
        if user is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
        return user

    @app.post("/auth/login", response_model=TokenRead)
    def login(payload: UserLogin, db=Depends(get_db)) -> dict[str, str]:
        user = repository.get_user_by_email(db, payload.email)
        if user is None or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        return {"access_token": create_access_token(user["id"]), "token_type": "bearer"}

    @app.get("/me", response_model=UserRead)
    def me(current_user=Depends(get_current_user)) -> dict[str, Any]:
        return current_user

    @app.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
    def create_application(
        payload: ApplicationCreate,
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        if payload.status != Status.planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new applications must start with planned status",
            )
        return repository.create_application(
            db,
            current_user["id"],
            payload.model_dump(mode="json"),
        )

    @app.get("/applications", response_model=list[ApplicationRead])
    def list_applications(
        status_filter: Status | None = Query(default=None, alias="status"),
        direction: Direction | None = None,
        priority: Priority | None = None,
        source: Source | None = None,
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> list[dict[str, Any]]:
        return repository.list_applications(
            db,
            current_user["id"],
            status=status_filter.value if status_filter else None,
            direction=direction.value if direction else None,
            priority=priority.value if priority else None,
            source=source.value if source else None,
        )

    @app.get("/applications/follow-ups", response_model=list[ApplicationRead])
    def list_follow_ups(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> list[dict[str, Any]]:
        return repository.list_follow_ups(db, current_user["id"], today=date.today().isoformat())

    @app.get("/applications/{application_id}", response_model=ApplicationRead)
    def get_application(
        application_id: int,
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        application = repository.get_application(db, current_user["id"], application_id)
        if application is None:
            raise HTTPException(status_code=404, detail="application not found")
        return application

    @app.patch("/applications/{application_id}", response_model=ApplicationRead)
    def update_application(
        application_id: int,
        payload: ApplicationUpdate,
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        current_application = repository.get_application(db, current_user["id"], application_id)
        if current_application is None:
            raise HTTPException(status_code=404, detail="application not found")

        updates = payload.model_dump(mode="json", exclude_unset=True)
        if "status" in updates:
            current_status = Status(current_application["status"])
            target_status = Status(updates["status"])
            if not is_valid_status_transition(current_status, target_status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=status_transition_error(current_status, target_status),
                )

        application = repository.update_application(
            db,
            current_user["id"],
            application_id,
            updates,
        )
        return application

    @app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_application(
        application_id: int,
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> None:
        if not repository.delete_application(db, current_user["id"], application_id):
            raise HTTPException(status_code=404, detail="application not found")

    @app.get("/stats/summary")
    def stats_summary(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        return repository.summary(db, current_user["id"])

    @app.get("/stats/funnel")
    def stats_funnel(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        return repository.funnel(db, current_user["id"])

    @app.get("/stats/weekly")
    def stats_weekly(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> list[dict[str, Any]]:
        return repository.weekly_activity(db, current_user["id"])

    @app.get("/stats/sources")
    def stats_sources(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> list[dict[str, Any]]:
        return repository.response_rate_by_source(db, current_user["id"])

    @app.get("/exports/applications.csv")
    def export_applications_csv(
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> Response:
        rows = repository.list_applications(db, current_user["id"])
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=repository.EXPORT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) or "" for field in repository.EXPORT_FIELDS})

        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="applications.csv"'},
        )

    @app.post("/imports/applications.csv", response_model=CsvImportReport)
    async def import_applications_csv(
        file: UploadFile = File(...),
        current_user=Depends(get_current_user),
        db=Depends(get_db),
    ) -> dict[str, Any]:
        raw_content = await file.read()
        try:
            decoded_content = raw_content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="csv file must be encoded as UTF-8",
            ) from exc

        reader = csv.DictReader(StringIO(decoded_content))
        errors: list[dict[str, Any]] = []
        imported = 0
        skipped_duplicates = 0

        if reader.fieldnames is None:
            return {"imported": 0, "skipped_duplicates": 0, "errors": [{"row": 1, "error": "empty csv"}]}

        for row_number, row in enumerate(reader, start=2):
            try:
                payload = ApplicationCreate.model_validate(_csv_payload(row))
            except ValidationError as exc:
                errors.append({"row": row_number, "error": _validation_error(exc)})
                continue

            if payload.status != Status.planned:
                errors.append(
                    {"row": row_number, "error": "status: new applications must start with planned status"}
                )
                continue

            data = payload.model_dump(mode="json")
            if repository.duplicate_application_exists(
                db,
                current_user["id"],
                data["company"],
                data["role"],
                data.get("link"),
            ):
                skipped_duplicates += 1
                continue

            repository.create_application(db, current_user["id"], data)
            imported += 1

        return {"imported": imported, "skipped_duplicates": skipped_duplicates, "errors": errors}

    return app


def _bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _csv_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in repository.CREATE_FIELDS:
        value = row.get(field)
        if value is None:
            continue
        value = value.strip()
        if value:
            payload[field] = value
    return payload


def _validation_error(exc: ValidationError) -> str:
    first_error = exc.errors()[0]
    location = ".".join(str(part) for part in first_error["loc"])
    return f"{location}: {first_error['msg']}"


app = create_app()
