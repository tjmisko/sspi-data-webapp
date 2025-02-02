import pytest
import requests
from sspi_flask_app.models.database.sspi_metadata import SSPIMetadata
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.api.resources.utilities import parse_json


@pytest.fixture(scope="session")
def test_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    yield SSPIMetadata(sspi_test_db)
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)


@pytest.fixture(scope="session")
def sspi_indicator_details(test_db):
    reponse = requests.get(
        "https://sspi.world/api/v1/query/sspi_metadata").json()
    metadata = parse_json(reponse)
    test_db.insert_many(metadata)
    indicator_details = test_db.indicator_details()
    yield indicator_details


@pytest.fixture(scope="session")
def sspi_aus_main_data(test_db):
    reponse = requests.get(
        "https://sspi.world/api/v1/query/sspi_main_data_v3?CountryCode=AUS"
    ).json()
    yield parse_json(reponse)


def test_integration_setup(sspi_indicator_details, sspi_aus_main_data):
    assert len(sspi_indicator_details) == 57
    assert len(sspi_aus_main_data) == 57


@pytest.fixture(scope="session")
def sspi_aus_2018(sspi_indicator_details, sspi_aus_main_data):
    yield SSPI(sspi_indicator_details, sspi_aus_main_data)


def test_sspi_structure_real_data(sspi_aus_2018):
    assert len(sspi_aus_2018.pillars) == 3
    assert len(sspi_aus_2018.categories) == 16
    assert len(sspi_aus_2018.indicators) == 57


def test_sspi_score_real_data(sspi_aus_2018):
    tol = 10**-2
    score_tree = sspi_aus_2018.score()
    assert abs(sspi_aus_2018.score() - 0.64) < tol
    pillar_scores = sspi_aus_2018.pillar_scores()
    assert abs(pillar_scores["SUS"] == 0.48) < tol
    assert abs(pillar_scores["MS"] == 0.64) < tol
    assert abs(pillar_scores["PG"] == 0.79) < tol
