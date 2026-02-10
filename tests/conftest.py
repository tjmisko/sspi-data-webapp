from sspi_flask_app import init_app
import pathlib
from config import TestConfig
import pytest

def pytest_ignore_collect(path, config):
    return any(".git/worktrees" in part for part in pathlib.Path(path).parts)

@pytest.fixture(scope="session")
def app():
    app = init_app(TestConfig)
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


