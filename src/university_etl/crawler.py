from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tldextract import extract as tld_extract

SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar", ".ppt", ".pptx",
)
SKIP_PATTERNS = ("login", "auth", "sso", "portal", "signin", "sign-in")

KEYWORDS = {
    "admissions": ["admissions", "admission", "apply", "application", "first-year", "freshman", "transfer", "international students"],
    "deadlines": ["deadline", "deadlines", "dates", "early decision", "early action", "regular decision", "priority date"],
    "tuition": ["tuition", "cost", "costs", "fees", "financial aid", "cost of attendance", "bursar", "student accounts"],
    "contact": ["contact", "phone", "email", "address", "office of admissions"],
}


@dataclass
class CrawledPage:
    url: str
    depth: int
    status_code: int
    content_type: str | None
    fetched_at: datetime
    title: str | None
    text: str
    headings: str
    anchors: list[tuple[str, str]]


def normalize_domain_to_url(domain: str) -> str:
    d = domain.strip().lower()
    d = d.replace("http://", "").replace("https://", "").strip("/")
    return f"https://{d}"


def registrable_domain(url: str) -> str:
    p = tld_extract(url)
    return f"{p.domain}.{p.suffix}" if p.suffix else p.domain


def same_registrable_domain(url: str, base_reg_domain: str) -> bool:
    return registrable_domain(url) == base_reg_domain


def _should_skip(url: str) -> bool:
    l = url.lower()
    return any(l.endswith(ext) for ext in SKIP_EXTENSIONS) or any(p in l for p in SKIP_PATTERNS)


def _score_text(haystack: str, words: list[str]) -> int:
    h = haystack.lower()
    score = 0
    for w in words:
        if w in h:
            score += 3 if " " in w else 2
    return score


def score_page(page: CrawledPage) -> dict[str, int]:
    haystack = " ".join([page.url, page.title or "", page.headings, page.text[:5000]])
    return {k: _score_text(haystack, v) for k, v in KEYWORDS.items()}


def crawl_domain(domain: str, max_depth: int = 2, max_pages: int = 50, timeout: int = 15) -> list[CrawledPage]:
    start_url = normalize_domain_to_url(domain)
    base_reg_domain = registrable_domain(start_url)
    q = deque([(start_url, 0)])
    visited: set[str] = set()
    pages: list[CrawledPage] = []

    session = requests.Session()
    session.headers.update({"User-Agent": "university-etl/1.0"})

    while q and len(pages) < max_pages:
        url, depth = q.popleft()
        if depth > max_depth or url in visited or _should_skip(url):
            continue
        visited.add(url)

        try:
            r = session.get(url, timeout=timeout, allow_redirects=True)
        except requests.RequestException:
            continue

        final_url = r.url
        if not same_registrable_domain(final_url, base_reg_domain):
            continue

        ctype = r.headers.get("Content-Type", "")
        if "text/html" not in ctype.lower():
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup(["script", "style", "noscript"]):
            s.extract()

        title = soup.title.get_text(" ", strip=True) if soup.title else None
        headings = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(re.compile("^h[1-3]$")))
        text = soup.get_text(" ", strip=True)

        anchors: list[tuple[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = urljoin(final_url, a["href"]).split("#")[0]
            if href.startswith("mailto:") or href.startswith("tel:"):
                continue
            if not href.startswith("http") or _should_skip(href):
                continue
            if not same_registrable_domain(href, base_reg_domain):
                continue
            anchor_text = a.get_text(" ", strip=True)
            anchors.append((href, anchor_text))
            if href not in visited and depth + 1 <= max_depth:
                q.append((href, depth + 1))

        pages.append(CrawledPage(
            url=final_url,
            depth=depth,
            status_code=r.status_code,
            content_type=ctype,
            fetched_at=datetime.now(timezone.utc),
            title=title,
            text=text,
            headings=headings,
            anchors=anchors,
        ))

    return pages


def select_relevant_pages(pages: list[CrawledPage], top_k: int = 5) -> dict[str, list[CrawledPage]]:
    scored = [(p, score_page(p)) for p in pages]
    out: dict[str, list[CrawledPage]] = {}
    for cat in ("admissions", "deadlines", "tuition", "contact"):
        ranked = sorted(scored, key=lambda x: x[1][cat], reverse=True)
        out[cat] = [p for p, s in ranked if s[cat] > 0][:top_k]
    return out
