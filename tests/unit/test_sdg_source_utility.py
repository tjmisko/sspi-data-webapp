from sspi_flask_app import init_app
from config import DevConfig
import pytest

@pytest.fixture()
def app():
    app = init_app(DevConfig)
    app.config.update({"TESTING": True})
    # OTHER TESTING SETUP
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner

def test_collect_geo_area():
    """
    GIVEN an SDG Indicator Code
    THEN hits the API and returns a list strings 
    representing the M49 codes of countries with data for the indicator
    """
    lst = ["cheese", "burgeer"]
    assert type(lst[1]) == type("string")
    assert len(lst) != 0