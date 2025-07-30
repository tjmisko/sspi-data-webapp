import pytest
from sspi_flask_app.api.resources.utilities import (
    score_indicator,
    group_by_indicator
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data
)
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture
def test_data():
    yield [
        {
            "DatasetCode": "UNSDG_TERRST",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_FRSHWT",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_MARINE",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_TERRST",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_FRSHWT",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_MARINE",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 50
        },
        {
            "DatasetCode": "UNSDG_TERRST",
            "CountryCode": "URU",
            "Year": 2017,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_FRSHWT",
            "CountryCode": "URU",
            "Year": 2017,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "DatasetCode": "UNSDG_MARINE",
            "CountryCode": "URU",
            "Year": 2017,
            "Value": 50,
            "Unit": "Index"
        }
    ]


@pytest.fixture
def test_extra_datasets():
    yield [
        {
            "DatasetCode": "LDAREA",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 7692024,  # Australia's land area in km^2
            "Unit": "km^2"
        },
        {
            "DatasetCode": "LDAREA",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 176215,  # Uruguay's land area in km^2
            "Unit": "km^2"
        }
    ]


@pytest.fixture
def test_junk():
    yield [
        {
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 7692024,  # Australia's land area in km^2
            "Unit": "km^2"
        },
        {
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 176215,  # Uruguay's land area in km^2
            "Unit": "km^2"
        }
    ]


def test_validate_datasets_list(test_data):
    sspi_clean_api_data.validate_dataset_list(test_data[0:5])
    with pytest.raises(InvalidDocumentFormatError) as e_info:
        sspi_clean_api_data.validate_dataset_list(test_data[0:6])
    assert "Unit" in str(e_info.value)


def test_group_by_indicator(test_data):
    indicator_document_list = group_by_indicator(test_data, "BIODIV")
    assert indicator_document_list[0]["IndicatorCode"] == "BIODIV"
    assert indicator_document_list[0]["CountryCode"] == "AUS"
    assert indicator_document_list[0]["Year"] == 2018
    assert indicator_document_list[0]["Datasets"][0]["DatasetCode"] == "UNSDG_TERRST"
    assert indicator_document_list[0]["Datasets"][1]["DatasetCode"] == "UNSDG_FRSHWT"
    assert indicator_document_list[0]["Datasets"][2]["DatasetCode"] == "UNSDG_MARINE"
    assert indicator_document_list[1]["IndicatorCode"] == "BIODIV"
    assert indicator_document_list[1]["CountryCode"] == "URU"
    assert indicator_document_list[1]["Year"] == 2018
    assert indicator_document_list[1]["Datasets"][0]["DatasetCode"] == "UNSDG_TERRST"
    assert indicator_document_list[1]["Datasets"][1]["DatasetCode"] == "UNSDG_FRSHWT"


def test_score_indicator(test_data):
    with pytest.raises(InvalidDocumentFormatError) as e_info:
        zipped_list, incomplete_list = score_indicator(
            test_data, "BIODIV",
            score_function=lambda UNSDG_TERRST, UNSDG_FRSHWT, UNSDG_MARINE: (UNSDG_TERRST + UNSDG_FRSHWT + UNSDG_MARINE) / 3,
            unit="Index",
        )
        assert "Unit" in str(e_info.value)
        assert "InvalidDocumentFormatError" in str(e_info.value)
    zipped_list, incomplete_list = score_indicator(
        [*test_data[0:3], *test_data[6:9]], "BIODIV",
        score_function=lambda UNSDG_TERRST, UNSDG_FRSHWT, UNSDG_MARINE: (UNSDG_TERRST + UNSDG_FRSHWT + UNSDG_MARINE) / 3,
        unit="Index"
    )
    assert len(zipped_list) == 2
    assert zipped_list[0]["CountryCode"] == "AUS"
    assert zipped_list[0]["Year"] == 2018
    assert zipped_list[0]["IndicatorCode"] == "BIODIV"
    assert zipped_list[1]["CountryCode"] == "URU"
    assert zipped_list[1]["Year"] == 2017
    assert zipped_list[1]["IndicatorCode"] == "BIODIV"


def test_score_indicator_with_extra_datasets(test_data, test_extra_datasets):
    def score_biodiv(UNSDG_TERRST, UNSDG_FRSHWT, UNSDG_MARINE):
        return (UNSDG_TERRST / 100 + UNSDG_FRSHWT / 100 + UNSDG_MARINE / 100 ) / 3

    zipped_list, incomplete_list = score_indicator(
        [*test_data[0:3], *test_data[6:9], *test_extra_datasets], "BIODIV",
        score_function=score_biodiv,
        unit="Index",
    )
    assert len(zipped_list) == 2
    assert zipped_list[0]["CountryCode"] == "AUS"
    assert zipped_list[0]["Year"] == 2018
    assert zipped_list[0]["IndicatorCode"] == "BIODIV"
    assert zipped_list[0].get("Datasets", None) is not None
    assert zipped_list[0]["Score"] == pytest.approx(0.5, rel=1e-4)
    assert len(zipped_list[0]["Datasets"]) == 4
    assert zipped_list[0]["Datasets"][3]["DatasetCode"] == "LDAREA"
    assert zipped_list[1]["CountryCode"] == "URU"
    assert zipped_list[1]["Year"] == 2017
    assert zipped_list[1]["IndicatorCode"] == "BIODIV"
    assert zipped_list[1].get("Datasets", None) is not None
    assert len(zipped_list[1]["Datasets"]) == 3
