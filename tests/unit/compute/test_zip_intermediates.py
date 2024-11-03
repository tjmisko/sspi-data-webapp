import pytest
from sspi_flask_app.api.resources.utilities import (
    zip_intermediates,
    append_goalpost_info,
    group_by_indicator
    # score_indicator_documents
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data
)
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture
def test_data():
    yield [
        {
            "IntermediateCode": "TERRST",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "FRSHWT",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "MARINE",
            "CountryCode": "AUS",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "TERRST",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "FRSHWT",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "MARINE",
            "CountryCode": "URU",
            "Year": 2018,
            "Value": 50
        },
        {
            "IntermediateCode": "TERRST",
            "CountryCode": "URU",
            "Year": 2017,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "FRSHWT",
            "CountryCode": "URU",
            "Year": 2017,
            "Value": 50,
            "Unit": "Index"
        },
        {
            "IntermediateCode": "MARINE",
            "CountryCode": "URU",
            "Year": 2017,
            "Value": 50,
            "Unit": "Index"
        }
    ]


def test_validate_intermediates_list(test_data):
    sspi_clean_api_data.validate_intermediates_list(test_data[0:5])
    with pytest.raises(InvalidDocumentFormatError) as e_info:
        sspi_clean_api_data.validate_intermediates_list(test_data[0:6])
    assert "Unit" in str(e_info.value)


def test_gp_intermediate_list(test_data):
    gp_intermediate_list = append_goalpost_info(test_data, "Score")
    assert gp_intermediate_list[0]["LowerGoalpost"] == 0
    assert gp_intermediate_list[0]["UpperGoalpost"] == 100
    assert gp_intermediate_list[0]["Score"] == 0.5
    assert gp_intermediate_list[1]["LowerGoalpost"] == 0
    assert gp_intermediate_list[1]["UpperGoalpost"] == 100
    assert gp_intermediate_list[1]["Score"] == 0.5
    assert gp_intermediate_list[2]["LowerGoalpost"] == 0
    assert gp_intermediate_list[2]["UpperGoalpost"] == 100
    assert gp_intermediate_list[2]["Score"] == 0.5
    assert gp_intermediate_list[3]["LowerGoalpost"] == 0
    assert gp_intermediate_list[3]["UpperGoalpost"] == 100
    assert gp_intermediate_list[3]["Score"] == 0.5
    assert gp_intermediate_list[4]["LowerGoalpost"] == 0
    assert gp_intermediate_list[4]["UpperGoalpost"] == 100
    assert gp_intermediate_list[4]["Score"] == 0.5


def test_group_by_indicator(test_data):
    indicator_document_list = group_by_indicator(test_data, "BIODIV")
    assert indicator_document_list[0]["IndicatorCode"] == "BIODIV"
    assert indicator_document_list[0]["CountryCode"] == "AUS"
    assert indicator_document_list[0]["Year"] == 2018
    assert indicator_document_list[0]["Intermediates"][0]["IntermediateCode"] == "TERRST"
    assert indicator_document_list[0]["Intermediates"][1]["IntermediateCode"] == "FRSHWT"
    assert indicator_document_list[0]["Intermediates"][2]["IntermediateCode"] == "MARINE"
    assert indicator_document_list[1]["IndicatorCode"] == "BIODIV"
    assert indicator_document_list[1]["CountryCode"] == "URU"
    assert indicator_document_list[1]["Year"] == 2018
    assert indicator_document_list[1]["Intermediates"][0]["IntermediateCode"] == "TERRST"
    assert indicator_document_list[1]["Intermediates"][1]["IntermediateCode"] == "FRSHWT"


def test_zip_intermediates(test_data):
    with pytest.raises(InvalidDocumentFormatError) as e_info:
        zipped_list = zip_intermediates(test_data,
                                        "BIODIV",
                                        ScoreFunction=lambda TERRST, FRSHWT, MARINE: TERRST/3 + FRSHWT/3 + MARINE/3,
                                        ScoreBy="Score")
        assert "Unit" in str(e_info.value)
        assert "InvalidDocumentFormatError" in str(e_info.value)
    zipped_list = zip_intermediates([*test_data[0:3], *test_data[6:9]],
                                    "BIODIV",
                                    ScoreFunction=lambda TERRST, FRSHWT, MARINE: TERRST/3 + FRSHWT/3 + MARINE/3,
                                    ScoreBy="Score")
    assert len(zipped_list) == 2
    assert zipped_list[0]["CountryCode"] == "AUS"
    assert zipped_list[0]["Year"] == 2018
    assert zipped_list[0]["IndicatorCode"] == "BIODIV"
    assert zipped_list[1]["CountryCode"] == "URU"
    assert zipped_list[1]["Year"] == 2017
    assert zipped_list[1]["IndicatorCode"] == "BIODIV"
