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


