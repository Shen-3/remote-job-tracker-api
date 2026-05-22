from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class Direction(str, Enum):
    python_backend = "python_backend"
    qa_automation = "qa_automation"
    data_analytics = "data_analytics"
    data_engineering = "data_engineering"
    csharp_dotnet = "csharp_dotnet"
    telegram_bots = "telegram_bots"
    freelance_automation = "freelance_automation"


class Status(str, Enum):
    planned = "planned"
    applied = "applied"
    recruiter_reply = "recruiter_reply"
    test_task = "test_task"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"
    paused = "paused"


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=160)
    direction: Direction
    status: Status = Status.planned
    link: HttpUrl | None = None
    salary: str | None = Field(default=None, max_length=80)
    hours_per_week: int | None = Field(default=None, ge=1, le=60)
    deadline: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: str | None = Field(default=None, max_length=1000)


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=2, max_length=120)
    role: str | None = Field(default=None, min_length=2, max_length=160)
    direction: Direction | None = None
    status: Status | None = None
    link: HttpUrl | None = None
    salary: str | None = Field(default=None, max_length=80)
    hours_per_week: int | None = Field(default=None, ge=1, le=60)
    deadline: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: str | None = Field(default=None, max_length=1000)


class ApplicationRead(ApplicationCreate):
    id: int
    created_at: str
    updated_at: str
