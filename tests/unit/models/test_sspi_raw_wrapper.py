import pytest

@pytest.fixture
def test_data():
    test_data_dict = {}
    yield test_data_dict
    
