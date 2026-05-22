from __future__ import annotations

from collections.abc import Generator
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status

from jobtracker import repository
from jobtracker.database import connect, init_db
from jobtracker.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate, Direction, Status


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Remote Job Tracker API",
        version="0.1.0",
        description="Track remote internship and junior job applications.",
    )

    def get_db() -> Generator:
        conn = connect(db_path)
        init_db(conn)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
    def create_application(payload: ApplicationCreate, db=Depends(get_db)) -> dict[str, Any]:
        return repository.create_application(db, payload.model_dump(mode="json"))

    @app.get("/applications", response_model=list[ApplicationRead])
    def list_applications(
        status_filter: Status | None = Query(default=None, alias="status"),
        direction: Direction | None = None,
        db=Depends(get_db),
    ) -> list[dict[str, Any]]:
        return repository.list_applications(
            db,
            status=status_filter.value if status_filter else None,
            direction=direction.value if direction else None,
        )

    @app.get("/applications/{application_id}", response_model=ApplicationRead)
    def get_application(application_id: int, db=Depends(get_db)) -> dict[str, Any]:
        application = repository.get_application(db, application_id)
        if application is None:
            raise HTTPException(status_code=404, detail="application not found")
        return application

    @app.patch("/applications/{application_id}", response_model=ApplicationRead)
    def update_application(
        application_id: int,
        payload: ApplicationUpdate,
        db=Depends(get_db),
    ) -> dict[str, Any]:
        application = repository.update_application(
            db,
            application_id,
            payload.model_dump(mode="json", exclude_unset=True),
        )
        if application is None:
            raise HTTPException(status_code=404, detail="application not found")
        return application

    @app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_application(application_id: int, db=Depends(get_db)) -> None:
        if not repository.delete_application(db, application_id):
            raise HTTPException(status_code=404, detail="application not found")

    @app.get("/stats/summary")
    def stats_summary(db=Depends(get_db)) -> dict[str, Any]:
        return repository.summary(db)

    return app


app = create_app()
