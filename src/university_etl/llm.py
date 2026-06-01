from __future__ import annotations

import json
import os

from pydantic import ValidationError

from .models import UniversityOutput


def try_llm_enhancement(base: UniversityOutput, page_text_blobs: list[str]) -> UniversityOutput:
    if not os.getenv("GEMINI_API_KEY"):
        return base

    try:
        from google import genai
    except ImportError:
        return base

    prompt = {
        "schema": UniversityOutput.model_json_schema(),
        "current": base.model_dump(mode="json"),
        "pages": page_text_blobs[:6],
        "instruction": "Return only JSON following schema. Keep unknowns null."
    }

    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=json.dumps(prompt),
        )
        txt = getattr(resp, "text", None)
        if not txt:
            return base
        parsed = json.loads(txt)
        return UniversityOutput.model_validate(parsed)
    except (ValidationError, json.JSONDecodeError, Exception):
        return base
