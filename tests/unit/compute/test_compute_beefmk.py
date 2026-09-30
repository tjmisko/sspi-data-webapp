from pathlib import Path

import frontmatter
import pytest

from sspi_flask_app.api.core.sspi.sus.ghg.beefmk import (
    BEEFMK_CONSUMPTION_LOWER_GOALPOST,
    BEEFMK_CONSUMPTION_UPPER_GOALPOST,
    BEEFMK_KG_PER_THOUSAND_TONNES,
    BEEFMK_PRODUCTION_LOWER_GOALPOST,
    BEEFMK_PRODUCTION_UPPER_GOALPOST,
    beef_production_kg_per_capita,
    score_beefmk,
)
from sspi_flask_app.api.resources.score_function_validator import (
    safe_eval,
    validate_score_function,
)
from sspi_flask_app.api.resources.utilities import goalpost, score_indicator

REPO_ROOT = Path(__file__).resolve().parents[3]
METHODOLOGY_PATH = REPO_ROOT / "methodology" / "sus" / "ghg" / "beefmk" / "methodology.md"
BFPROD_DOC_PATH = REPO_ROOT / "datasets" / "unfao" / "unfao_bfprod" / "documentation.md"

# Stored values from sspi_clean_api_data (UNFAO_BFPROD, UNFAO_BFCONS, WB_POPULN).
USA_2022_BFPROD_THOUSAND_TONNES = 12891
USA_2022_BFCONS_KG_PER_CAPITA = 38.01
USA_2022_POPULATION = 334017321
URY_2022_BFPROD_THOUSAND_TONNES = 616
URY_2022_BFCONS_KG_PER_CAPITA = 15.44
URY_2022_POPULATION = 3390913

UNITS = {
    "UNFAO_BFPROD": "1000 t",
    "UNFAO_BFCONS": "kg/capita/year",
    "WB_POPULN": "Population",
}


def make_doc(dataset_code, country_code, year, value):
    return {
        "DatasetCode": dataset_code,
        "CountryCode": country_code,
        "Year": year,
        "Value": value,
        "Unit": UNITS[dataset_code],
    }


def country_year_docs(country_code, year, production, consumption, population):
    return [
        make_doc("UNFAO_BFPROD", country_code, year, production),
        make_doc("UNFAO_BFCONS", country_code, year, consumption),
        make_doc("WB_POPULN", country_code, year, population),
    ]


@pytest.fixture
def usa_2022_docs():
    yield country_year_docs(
        "USA", 2022,
        USA_2022_BFPROD_THOUSAND_TONNES,
        USA_2022_BFCONS_KG_PER_CAPITA,
        USA_2022_POPULATION,
    )


def scores_by_country_year(scored_list):
    return {(doc["CountryCode"], doc["Year"]): doc["Score"] for doc in scored_list}


def test_should_convert_thousand_tonnes_to_kilograms_when_reading_module_constant():
    assert BEEFMK_KG_PER_THOUSAND_TONNES == 1_000_000


def test_should_give_usa_2022_about_38_6_kg_per_capita_when_production_is_in_thousand_tonnes():
    kg_per_capita = beef_production_kg_per_capita(
        USA_2022_BFPROD_THOUSAND_TONNES, USA_2022_POPULATION
    )
    assert kg_per_capita == pytest.approx(38.6, abs=0.05)


def test_should_score_usa_2022_below_saturation_when_computed_from_fixture(usa_2022_docs):
    scored, incomplete = score_indicator(
        usa_2022_docs, "BEEFMK", score_function=score_beefmk, unit="Index"
    )
    assert incomplete == []
    score = scores_by_country_year(scored)[("USA", 2022)]
    expected_production = (50 - 38.594) / 50
    expected_consumption = (50 - USA_2022_BFCONS_KG_PER_CAPITA) / 50
    assert score == pytest.approx((expected_production + expected_consumption) / 2, abs=1e-3)
    assert score == pytest.approx(0.234, abs=1e-3)
    assert 0.0 < score < 1.0


def test_should_not_saturate_production_subscore_when_production_is_large():
    production_score = goalpost(
        beef_production_kg_per_capita(USA_2022_BFPROD_THOUSAND_TONNES, USA_2022_POPULATION),
        BEEFMK_PRODUCTION_LOWER_GOALPOST,
        BEEFMK_PRODUCTION_UPPER_GOALPOST,
    )
    assert production_score < 0.5


def test_should_clamp_production_subscore_to_zero_when_major_exporter_exceeds_lower_goalpost():
    # URY 2022 produces about 182 kg per person, far past the 50 kg goalpost.
    score = score_beefmk(
        URY_2022_BFPROD_THOUSAND_TONNES, URY_2022_BFCONS_KG_PER_CAPITA, URY_2022_POPULATION
    )
    assert score == pytest.approx((0.0 + (50 - URY_2022_BFCONS_KG_PER_CAPITA) / 50) / 2)


def test_should_score_one_when_country_produces_and_consumes_no_beef():
    assert score_beefmk(0, 0, 1_000_000) == pytest.approx(1.0)


def test_should_score_zero_when_both_measures_reach_fifty_kg_per_capita():
    # 50 kg per person over one million people is 50,000,000 kg, or 50 thousand tonnes.
    assert score_beefmk(50, 50, 1_000_000) == pytest.approx(0.0)


def test_should_land_in_incomplete_list_when_population_is_missing(usa_2022_docs):
    docs_without_population = [d for d in usa_2022_docs if d["DatasetCode"] != "WB_POPULN"]
    scored, incomplete = score_indicator(
        docs_without_population, "BEEFMK", score_function=score_beefmk, unit="Index"
    )
    assert scored == []
    assert len(incomplete) == 1


def test_should_score_each_country_year_independently_when_fixture_has_two_countries(usa_2022_docs):
    docs = usa_2022_docs + country_year_docs(
        "URY", 2022,
        URY_2022_BFPROD_THOUSAND_TONNES,
        URY_2022_BFCONS_KG_PER_CAPITA,
        URY_2022_POPULATION,
    )
    scored, _ = score_indicator(docs, "BEEFMK", score_function=score_beefmk, unit="Index")
    scores = scores_by_country_year(scored)
    assert scores[("USA", 2022)] == pytest.approx(0.234, abs=1e-3)
    assert scores[("URY", 2022)] == pytest.approx(0.3456)


def test_should_match_module_goalposts_when_reading_methodology_front_matter():
    metadata = frontmatter.load(METHODOLOGY_PATH).metadata
    assert metadata["LowerGoalpost"] == BEEFMK_PRODUCTION_LOWER_GOALPOST
    assert metadata["UpperGoalpost"] == BEEFMK_PRODUCTION_UPPER_GOALPOST
    assert (BEEFMK_CONSUMPTION_LOWER_GOALPOST, BEEFMK_CONSUMPTION_UPPER_GOALPOST) == (50, 0)


def test_should_agree_with_compute_route_when_evaluating_methodology_score_function(usa_2022_docs):
    metadata = frontmatter.load(METHODOLOGY_PATH).metadata
    validated = validate_score_function(
        metadata["ScoreFunction"], set(metadata["DatasetCodes"])
    )
    values = {doc["DatasetCode"]: doc["Value"] for doc in usa_2022_docs}
    assert safe_eval(validated, values) == pytest.approx(score_beefmk(**values))


def test_should_describe_bfprod_as_total_thousand_tonnes_when_documentation_is_read():
    metadata = frontmatter.load(BFPROD_DOC_PATH).metadata
    assert metadata["Unit"] == "1000 t"
    assert "thousands of tonnes" in metadata["Description"]
    assert "kilograms per person, in" not in metadata["Description"]
