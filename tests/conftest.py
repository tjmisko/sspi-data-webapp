from sspi_flask_app import init_app
from config import DevConfig
from sspi_flask_app import init_app
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