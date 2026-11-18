"""
Every Indicator methodology.md ScoreFunction must be runnable by the custom
SSPI engine: it must validate against the indicator's own DatasetCodes.
"""
from pathlib import Path

import frontmatter
import pytest

from sspi_flask_app.api.resources.score_function_validator import (
    validate_score_function,
)

METHODOLOGY_DIR = Path(__file__).resolve().parents[3] / "methodology"


def _load_indicators() -> list[dict]:
    indicators = []
    for path in sorted(METHODOLOGY_DIR.rglob("methodology.md")):
        metadata = frontmatter.load(str(path)).metadata
        if metadata.get("ItemType") == "Indicator":
            indicators.append(metadata)
    return indicators


INDICATORS = _load_indicators()


def test_should_find_indicator_methodology_files_when_scanning_methodology_dir():
    assert len(INDICATORS) > 0


@pytest.mark.parametrize(
    "metadata",
    INDICATORS,
    ids=[m["ItemCode"] for m in INDICATORS],
)
def test_should_validate_score_function_when_checked_against_own_dataset_codes(metadata):
    score_function = metadata.get("ScoreFunction")
    dataset_codes = set(metadata.get("DatasetCodes") or [])
    assert isinstance(score_function, str), f"{metadata['ItemCode']} has no ScoreFunction"
    validate_score_function(score_function, dataset_codes)
