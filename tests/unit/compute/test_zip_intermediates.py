import pytest
from sspi_flask_app.api.resources.utilities import zip_intermediates, append_goalpost_info, group_by_indicator, score_indicator_documents
from ... import sspi_clean_api_data, sspi_metadata

@pytest.fixture
def test_data():
    yield [
        {"IntermediateCode": "TERRST", "CountryCode": "AUS", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "FRSHWT", "CountryCode": "AUS", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "MARINE", "CountryCode": "AUS", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "TERRST", "CountryCode": "URU", "Year": 2018, "Value": 0.5, "Unit": "Index"},
        {"IntermediateCode": "FRSHWT", "CountryCode": "URU", "Year": 2018, "Value": 0.5, "Unit": "Index"}
    ]

def test_validate_intermediates_list(test_data):
    assert sspi_clean_api_data.validate_intermediates_list(test_data[0]) == True
    assert sspi_clean_api_data.validate_intermediates_list(test_data[1]) == True
    assert sspi_clean_api_data.validate_intermediates_list(test_data[2]) == True
    assert sspi_clean_api_data.validate_intermediates_list(test_data[3]) == True
    assert sspi_clean_api_data.validate_intermediates_list(test_data[4]) == True

def test_gp_intermediate_list(test_data):
    gp_intermediate_list = append_goalpost_info(test_data)
    assert gp_intermediate_list[0]["LowerGoalpost"] == 0
    assert gp_intermediate_list[0]["UpperGoalpost"] == 1
    assert gp_intermediate_list[0]["Score"] == 0.5
    assert gp_intermediate_list[1]["LowerGoalpost"] == 0
    assert gp_intermediate_list[1]["UpperGoalpost"] == 1
    assert gp_intermediate_list[1]["Score"] == 0.5
    assert gp_intermediate_list[2]["LowerGoalpost"] == 0
    assert gp_intermediate_list[2]["UpperGoalpost"] == 1
    assert gp_intermediate_list[2]["Score"] == 0.5
    assert gp_intermediate_list[3]["LowerGoalpost"] == 0
    assert gp_intermediate_list[3]["UpperGoalpost"] == 1
    assert gp_intermediate_list[3]["Score"] == 0.5
    assert gp_intermediate_list[4]["LowerGoalpost"] == 0
    assert gp_intermediate_list[4]["UpperGoalpost"] == 1
    assert gp_intermediate_list[4]["Score"] == 0.5
    
def test_group_by_indicator(test_data):
    indicator_document_list = group_by_indicator(test_data, "BIODIV")
    assert indicator_document_list[0]["IndicatorCode"] == "BIODIV"
    assert indicator_document_list[0]["CountryCode"] == "AUS"
    assert indicator_document_list[0]["Year"] == 2018
    assert indicator_document_list[0]["Intermediates"][0]["IntermediateCode"] == "TERRST"
    assert indicator_document_list[0]["Intermediates"][1]["IntermediateCode"] == "FRSHWT"
    assert indicator_document_list[0]["Intermediates"][2]["IntermediateCode"] == "MARINE"
    assert indicator_document_list[1]["IndicatorCode"] == "SSPI"
    assert indicator_document_list[1]["CountryCode"] == "URU"
    assert indicator_document_list[1]["Year"] == 2018
    assert indicator_document_list[1]["Intermediates"][0]["IntermediateCode"] == "TERRST"
    assert indicator_document_list[1]["Intermediates"][1]["IntermediateCode"] == "FRSHWT"
