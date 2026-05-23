from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


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


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Source(str, Enum):
    hh = "hh"
    habr = "habr"
    tbank = "tbank"
    yandex = "yandex"
    vk = "vk"
    ozon = "ozon"
    freelance = "freelance"
    direct = "direct"


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=160)
    direction: Direction
    status: Status = Status.planned
    priority: Priority = Priority.medium
    source: Source = Source.direct
    link: HttpUrl | None = None
    salary: str | None = Field(default=None, max_length=80)
    hours_per_week: int | None = Field(default=None, ge=1, le=60)
    deadline: date | None = None
    next_action_at: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=2, max_length=120)
    role: str | None = Field(default=None, min_length=2, max_length=160)
    direction: Direction | None = None
    status: Status | None = None
    priority: Priority | None = None
    source: Source | None = None
    link: HttpUrl | None = None
    salary: str | None = Field(default=None, max_length=80)
    hours_per_week: int | None = Field(default=None, ge=1, le=60)
    deadline: date | None = None
    next_action_at: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ApplicationRead(ApplicationCreate):
    id: int
    created_at: str
    updated_at: str


class UserRegister(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: int
    email: str
    created_at: str


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CsvImportError(BaseModel):
    row: int
    error: str


class CsvImportReport(BaseModel):
    imported: int
    skipped_duplicates: int
    errors: list[CsvImportError]
