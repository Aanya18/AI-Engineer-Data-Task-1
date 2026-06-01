import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from university_etl.models import UniversityOutput


def test_sample_output_validates() -> None:
    p = Path("samples/sample_output_provided_universities.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 3
    for item in data:
        UniversityOutput.model_validate(item)
