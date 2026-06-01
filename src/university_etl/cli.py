from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .pipeline import run_pipeline


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="University admissions/tuition ETL")
    parser.add_argument("domains", nargs="*", help="University domains")
    parser.add_argument("--input-file", type=Path, help="File with one domain per line")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--use-llm", action="store_true", help="Enable optional Gemini enhancement")
    parser.add_argument("--max-pages", type=int, default=50)
    args = parser.parse_args()

    domains = list(args.domains)
    if args.input_file:
        domains.extend([l.strip() for l in args.input_file.read_text(encoding="utf-8").splitlines() if l.strip()])
    if not domains:
        raise SystemExit("No domains provided")

    outputs = [run_pipeline(d, use_llm=args.use_llm, max_pages=args.max_pages).model_dump(mode="json") for d in domains]
    args.out.write_text(json.dumps(outputs, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
