import pytest
from sspi_flask_app.models.database.sspi_metadata import SSPIMetadata
from sspi_flask_app.models.database import sspidb


@pytest.fixture(scope="session")
def test_metadata_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    yield SSPIMetadata(sspi_test_db)
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)


@pytest.fixture(scope="session")
def sspi_indicator_details(app, test_metadata_db):
    with app.app_context():
        test_metadata_db.load()
    indicator_details = test_metadata_db.indicator_details()
    yield indicator_details


def test_frontmatter_is_valid(sspi_indicator_details):
    assert len(sspi_indicator_details) > 0
