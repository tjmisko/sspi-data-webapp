from pathlib import Path
from types import SimpleNamespace

import frontmatter
import pytest

from sspi_flask_app.api.resources.score_function_validator import (
    safe_eval,
    validate_score_function,
)
from sspi_flask_app.api.resources.utilities import goalpost, score_indicator
from sspi_flask_app.models.database.sspi_metadata import SSPIMetadata

REPO_ROOT = Path(__file__).resolve().parents[3]
METHODOLOGY_PATH = REPO_ROOT / "methodology" / "sus" / "wst" / "mswgen" / "methodology.md"
EPI_MSWGEN_DOC_PATH = REPO_ROOT / "datasets" / "epi" / "epi_mswgen" / "documentation.md"

# Stored EPI_MSWGEN 2018 values: a high-waste and a low-waste country.
USA_2018_EPI_MSWGEN = 13.3
ETH_2018_EPI_MSWGEN = 89.2


@pytest.fixture(scope="module")
def methodology():
    return frontmatter.load(METHODOLOGY_PATH).metadata


@pytest.fixture(scope="module")
def metadata_goalposts(methodology):
    # Read goalposts the way compute_mswgen does: sspi_metadata.get_goalposts.
    stub_metadata = SimpleNamespace(get_indicator_detail=lambda code: methodology)
    return SSPIMetadata.get_goalposts(stub_metadata, "MSWGEN")


def epi_mswgen_doc(country_code, year, value):
    return {
        "DatasetCode": "EPI_MSWGEN",
        "CountryCode": country_code,
        "Year": year,
        "Value": value,
        "Unit": "Index",
    }


def score_with_route_logic(value, goalposts):
    lower_goalpost, upper_goalpost = goalposts
    return goalpost(value, lower_goalpost, upper_goalpost)


def test_should_run_goalposts_from_zero_to_one_hundred_when_front_matter_is_parsed(methodology):
    assert methodology["LowerGoalpost"] == 0
    assert methodology["UpperGoalpost"] == 100


def test_should_return_lower_then_upper_goalpost_when_compute_route_reads_metadata(metadata_goalposts):
    assert metadata_goalposts == (0, 100)


def test_should_score_higher_when_epi_score_is_higher(metadata_goalposts):
    low = score_with_route_logic(USA_2018_EPI_MSWGEN, metadata_goalposts)
    high = score_with_route_logic(ETH_2018_EPI_MSWGEN, metadata_goalposts)
    assert high > low
    assert low == pytest.approx(0.133)
    assert high == pytest.approx(0.892)


@pytest.mark.parametrize("epi_score, expected", [(0, 0.0), (50, 0.5), (100, 1.0)])
def test_should_map_epi_score_linearly_when_value_is_on_the_scale(metadata_goalposts, epi_score, expected):
    assert score_with_route_logic(epi_score, metadata_goalposts) == pytest.approx(expected)


@pytest.mark.parametrize("epi_score, expected", [(-5, 0.0), (104, 1.0)])
def test_should_clamp_when_epi_score_is_off_the_scale(metadata_goalposts, epi_score, expected):
    assert score_with_route_logic(epi_score, metadata_goalposts) == pytest.approx(expected)


def test_should_increase_monotonically_when_evaluating_methodology_score_function(methodology):
    validated = validate_score_function(
        methodology["ScoreFunction"], set(methodology["DatasetCodes"])
    )
    epi_scores = [0, 13.3, 50, 89.2, 100]
    scores = [safe_eval(validated, {"EPI_MSWGEN": value}) for value in epi_scores]
    assert scores == sorted(scores)
    assert scores[0] == pytest.approx(0.0)
    assert scores[-1] == pytest.approx(1.0)


def test_should_rank_low_waste_country_first_when_scoring_documents(metadata_goalposts):
    docs = [
        epi_mswgen_doc("USA", 2018, USA_2018_EPI_MSWGEN),
        epi_mswgen_doc("ETH", 2018, ETH_2018_EPI_MSWGEN),
    ]
    scored, _ = score_indicator(
        docs, "MSWGEN",
        score_function=lambda EPI_MSWGEN: score_with_route_logic(EPI_MSWGEN, metadata_goalposts),
        unit="Index",
    )
    scores = {doc["CountryCode"]: doc["Score"] for doc in scored}
    assert scores["ETH"] > scores["USA"]


def test_should_not_describe_an_epi_score_as_kilograms_when_methodology_is_read(methodology):
    assert "kg/capita/year" not in methodology["Description"]
    assert "higher scores mean" in methodology["Description"]


def test_should_describe_dataset_as_zero_to_one_hundred_score_when_documentation_is_read():
    metadata = frontmatter.load(EPI_MSWGEN_DOC_PATH).metadata
    assert metadata["Unit"] == "Index"
    assert "0 to 100" in metadata["Description"]
