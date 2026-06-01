# University ETL

Python ETL pipeline that starts from a university domain, crawls the same registrable domain (depth <= 2), discovers Admissions and Tuition/Cost pages via keyword scoring, and extracts structured outputs validated by Pydantic.

## Install

```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in project root:

```env
GEMINI_API_KEY=your_key_here
```

- `GEMINI_API_KEY` is optional.
- Required only when running with `--use-llm`.
- Pipeline works without Gemini and falls back to deterministic extraction.

## Run

```bash
python -m university_etl.cli bucknell.edu udc.edu salisbury.edu --out outputs.json
python -m university_etl.cli --input-file samples/provided_domains.txt --out outputs.json
python -m university_etl.cli bucknell.edu --use-llm --out bucknell.json
```

### Windows PowerShell (recommended)

```powershell
$env:PYTHONPATH='src'
python -m university_etl.cli --input-file samples/provided_domains.txt --out outputs.json
python -m university_etl.cli --input-file samples/provided_domains.txt --use-llm --out outputs_llm.json
```

## Test / Validation

Run schema validation test:

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Expected result:
- `1 passed`

## Approach

- BFS crawl from `https://<domain>` with max depth `2` and configurable max pages.
- Stay in same registrable domain only.
- Skip auth/portal/login-like pages and non-HTML/binary resources.
- Score pages using URL, title, headings, and body for admissions/deadlines/tuition/contact categories.
- Deterministic extraction for contact, tuition amounts, and admission deadlines.
- Optional Gemini enhancement (`--use-llm`) with strict schema re-validation.

## Key decisions

- No site-specific final URLs are hardcoded.
- Unknown values remain `null`.
- Dates are populated only when explicit year exists.

## Interview Evaluation Process

Use this checklist to demonstrate the pipeline in an interview:

1. Explain constraints:
- Starts from domain only.
- No hardcoded final admissions/tuition URLs.
- Depth capped at 2.
- Same registrable domain enforced.

2. Show deterministic first:
- Run without `--use-llm`.
- Inspect discovered `admissions_pages` and `tuition_pages`.

3. Show optional LLM enhancement:
- Add `.env` with `GEMINI_API_KEY`.
- Re-run with `--use-llm`.
- Confirm output still validates via Pydantic.

4. Validate quality gate:
- Run `pytest`.
- Mention that sample JSON must pass strict schema validation.

5. Discuss tradeoffs:
- Deterministic extraction is robust and explainable.
- LLM helps with messy layouts/tables.
- Unknown fields are intentionally kept `null` to avoid fabrication.

## Assumptions and limitations

- `requests + BeautifulSoup` only; no required JS rendering.
- Heuristic extraction may miss complex table layouts without LLM enhancement.
- Gemini is optional and never trusted without Pydantic validation.
