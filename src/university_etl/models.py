from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl


class ContactInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: HttpUrl | None = None


class PageMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    url: HttpUrl
    title: str | None = None
    purpose: Literal["overview", "admissions", "tuition", "deadlines", "contact", "other"]
    discovered_depth: int
    status_code: int
    fetched_at: dt.datetime
    content_type: str | None = None


class TuitionItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    label: str
    amount: Decimal | None = None
    currency: Literal["USD", "INR"] | None = None
    period: Literal["annual", "semester", "credit_hour"] | None = None
    residency: Literal["in_state", "out_of_state"] | None = None
    student_level: Literal["undergraduate", "graduate"] | None = None
    notes: str | None = None
    source_url: HttpUrl


class AdmissionDeadline(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    label: str
    term: str | None = None
    student_type: str | None = None
    date: dt.date | None = None
    raw_text: str
    source_url: HttpUrl


class UniversityOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    input_domain: str
    university_name: str | None = None
    overview: str | None = None
    contact: ContactInfo
    admissions_pages: list[HttpUrl]
    tuition_pages: list[HttpUrl]
    tuition_items: list[TuitionItem]
    admission_deadlines: list[AdmissionDeadline]
    source_pages: list[PageMetadata]

