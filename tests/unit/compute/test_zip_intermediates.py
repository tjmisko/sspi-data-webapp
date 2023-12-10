import pytest
from zip_intermediates import zip_intermediates

@pytest.fixture
def test_data():
    yield [
        {"IntermediateCode": "TERRST", "CountryCode": "AUS", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "FRSHWT", "CountryCode": "AUS", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "MARINE", "CountryCode": "AUS", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "TERRST", "CountryCode": "URU", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "FRSHWT", "CountryCode": "URU", "Year": 2018, "Value": 0.5, "Unit": "Index"}
    ]
  

