from sspi_flask_app import init_app
from config import TestConfig
from sspi_flask_app import init_app
import pytest

@pytest.fixture(scope="session")
def app():
    app = init_app(TestConfig)
    app.config.update({"TESTING": True})
    # OTHER TESTING SETUP
    # Load in SSPI DATA
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
