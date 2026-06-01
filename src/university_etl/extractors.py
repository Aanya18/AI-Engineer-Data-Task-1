from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from .crawler import CrawledPage
from .models import AdmissionDeadline, ContactInfo, TuitionItem

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
MONEY_RE = re.compile(
    r"(?:(?P<usd>\$)\s?(?P<usd_amt>[0-9]{1,3}(?:,[0-9]{3})*(?:\.\d{1,2})?)|(?P<inr>(?:INR|Rs\.?|?))\s?(?P<inr_amt>[0-9]{1,3}(?:,[0-9]{3})*(?:\.\d{1,2})?))",
    re.I,
)
MONTH_DAY_RE = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,\s*(20\d{2}))?\b", re.I)
DAY_MONTH_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s*(20\d{2})?\b", re.I)


def extract_contact(pages: list[CrawledPage]) -> ContactInfo:
    text = " ".join(p.text[:3000] for p in pages)
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)

    address = None
    for chunk in re.split(r"\s{2,}|\.\s+", text):
        line = chunk.strip()
        if re.search(r"\b\d{2,6}\s+\w+", line) and re.search(r"\b[A-Z]{2}\b", line):
            address = line[:180]
            break

    return ContactInfo(
        address=address,
        phone=phone.group(0) if phone else None,
        email=email.group(0) if email else None,
        website=pages[0].url if pages else None,
    )


def _infer_period(text: str) -> str | None:
    t = text.lower()
    if "per credit" in t or "credit hour" in t:
        return "credit_hour"
    if "semester" in t or "term" in t:
        return "semester"
    if "trimester" in t:
        return "semester"
    if "annual" in t or "year" in t:
        return "annual"
    return None


def _infer_residency(text: str) -> str | None:
    t = text.lower()
    if "in-state" in t or "resident" in t:
        return "in_state"
    if "out-of-state" in t or "nonresident" in t:
        return "out_of_state"
    return None


def _infer_level(text: str) -> str | None:
    t = text.lower()
    if "undergraduate" in t:
        return "undergraduate"
    if "graduate" in t:
        return "graduate"
    return None


def extract_tuition_items(tuition_pages: list[CrawledPage]) -> list[TuitionItem]:
    items: list[TuitionItem] = []
    seen: set[tuple[str, str]] = set()

    for p in tuition_pages:
        sentences = re.split(r"(?<=[.!?])\s+", p.text)
        for s in sentences:
            if not any(k in s.lower() for k in ["tuition", "fee", "cost", "attendance", "credit"]):
                continue
            for m in MONEY_RE.finditer(s):
                raw = (m.group("usd_amt") or m.group("inr_amt") or "").replace(",", "")
                try:
                    amount = Decimal(raw)
                except InvalidOperation:
                    amount = None
                currency = "USD" if m.group("usd") else "INR" if m.group("inr") else None
                label = s[:120]
                key = (label, p.url)
                if key in seen:
                    continue
                seen.add(key)
                items.append(TuitionItem(
                    label=label,
                    amount=amount,
                    currency=currency if amount is not None else None,
                    period=_infer_period(s),
                    residency=_infer_residency(s),
                    student_level=_infer_level(s),
                    notes=None,
                    source_url=p.url,
                ))

    return items


def extract_deadlines(deadline_pages: list[CrawledPage]) -> list[AdmissionDeadline]:
    out: list[AdmissionDeadline] = []

    for p in deadline_pages:
        for s in re.split(r"(?<=[.!?])\s+", p.text):
            if "deadline" not in s.lower() and "early action" not in s.lower() and "regular decision" not in s.lower():
                continue
            match = MONTH_DAY_RE.search(s)
            parsed_date = None
            if match and match.group(3):
                month, day, year = match.group(1), int(match.group(2)), int(match.group(3))
                try:
                    parsed_date = date.fromisoformat(f"{year:04d}-{_month_to_num(month):02d}-{day:02d}")
                except ValueError:
                    parsed_date = None
            else:
                alt = DAY_MONTH_RE.search(s)
                if alt and alt.group(3):
                    day, month, year = int(alt.group(1)), alt.group(2), int(alt.group(3))
                    try:
                        parsed_date = date.fromisoformat(f"{year:04d}-{_month_to_num(month):02d}-{day:02d}")
                    except ValueError:
                        parsed_date = None

            term = "fall" if "fall" in s.lower() else "spring" if "spring" in s.lower() else None
            student_type = "international" if "international" in s.lower() else "transfer" if "transfer" in s.lower() else "first-year" if "first-year" in s.lower() else None
            label = "application deadline" if "deadline" in s.lower() else "admission date"

            out.append(AdmissionDeadline(
                label=label,
                term=term,
                student_type=student_type,
                date=parsed_date,
                raw_text=s[:220],
                source_url=p.url,
            ))

    return out


def _month_to_num(month: str) -> int:
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
    return months[month.lower()]
