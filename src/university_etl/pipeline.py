from __future__ import annotations

from .crawler import crawl_domain, select_relevant_pages
from .extractors import extract_contact, extract_deadlines, extract_tuition_items
from .llm import try_llm_enhancement
from .models import PageMetadata, UniversityOutput


def _unique_urls(pages):
    seen = set()
    out = []
    for p in pages:
        if p.url in seen:
            continue
        seen.add(p.url)
        out.append(p.url)
    return out


def run_pipeline(domain: str, use_llm: bool = False, max_pages: int = 50) -> UniversityOutput:
    pages = crawl_domain(domain=domain, max_depth=2, max_pages=max_pages)
    relevant = select_relevant_pages(pages)

    admissions = relevant.get("admissions", [])
    tuition = relevant.get("tuition", [])
    deadlines_pages = relevant.get("deadlines", admissions)
    contact_pages = relevant.get("contact", pages[:3])

    contact = extract_contact(contact_pages)
    tuition_items = extract_tuition_items(tuition)
    deadlines = extract_deadlines(deadlines_pages)

    university_name = pages[0].title.split("|")[0].strip() if pages and pages[0].title else None
    overview = pages[0].text[:600] if pages else None

    source_pages: list[PageMetadata] = []
    picked_urls = {p.url: "other" for p in pages[:30]}
    for p in admissions:
        picked_urls[p.url] = "admissions"
    for p in tuition:
        picked_urls[p.url] = "tuition"
    for p in deadlines_pages:
        if picked_urls.get(p.url) == "other":
            picked_urls[p.url] = "deadlines"
    for p in contact_pages:
        if picked_urls.get(p.url) == "other":
            picked_urls[p.url] = "contact"

    page_lookup = {p.url: p for p in pages}
    for url, purpose in picked_urls.items():
        p = page_lookup.get(url)
        if not p:
            continue
        source_pages.append(PageMetadata(
            url=p.url,
            title=p.title,
            purpose=purpose,
            discovered_depth=p.depth,
            status_code=p.status_code,
            fetched_at=p.fetched_at,
            content_type=p.content_type,
        ))

    output = UniversityOutput(
        input_domain=domain,
        university_name=university_name,
        overview=overview,
        contact=contact,
        admissions_pages=_unique_urls(admissions),
        tuition_pages=_unique_urls(tuition),
        tuition_items=tuition_items,
        admission_deadlines=deadlines,
        source_pages=source_pages,
    )

    if use_llm:
        output = try_llm_enhancement(output, [p.text[:6000] for p in pages])

    return output
