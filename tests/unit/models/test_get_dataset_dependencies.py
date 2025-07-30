import pytest
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.database.sspi_metadata import SSPIMetadata

@pytest.fixture(scope="function")
def sspi_metadata():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    sspi_metadata = SSPIMetadata(sspi_test_db)
    sspi_metadata.insert_many([
        {
            "DocumentType": "IndicatorDetail",
            "Metadata": {
                "Children": [],
                "DatasetCodes": [
                    "UNSDG_MARINE",
                    "UNSDG_TERRST",
                    "UNSDG_FRSHWT"
                ],
                "Description": "Percentage of important sites for terrestrial, freshwater, and marine biodiversity that are covered by protected areas, by ecosystem type.",
                "DocumentType": "IndicatorDetail",
                "Footnote": None,
                "Indicator": "Biodiversity Protection",
                "IndicatorCode": "BIODIV",
                "Inverted": False,
                "ItemCode": "BIODIV",
                "ItemName": "Biodiversity Protection",
                "ItemOrder": 0,
                "ItemType": "Indicator",
                "LowerGoalpost": None,
                "Policy": "Protection of Biodiversity",
                "SourceOrganization": "UN SDG",
                "SourceOrganizationIndicatorCode": None,
                "SourceOrganizationURL": "https://unstats.un.org/sdgapi/swagger/",
                "TreePath": "sspi/sus/eco/biodiv",
                "UpperGoalpost": None
            }
        },
        {
            "DocumentType": "IndicatorDetail",
            "Metadata": {
                "Children": [],
                "DatasetCodes": [
                    "UNSDG_REDLST"
                ],
                "Description": "Measures the level of extinction risk across species within a country. Index values of 1 represent all species qualifying as having an extinction risk of “least concern,” while values of 0 represent all species having gone extinct.",
                "DocumentType": "IndicatorDetail",
                "Footnote": None,
                "Indicator": "IUCN Red List Index",
                "IndicatorCode": "REDLST",
                "Inverted": False,
                "ItemCode": "REDLST",
                "ItemName": "IUCN Red List Index",
                "ItemOrder": 1,
                "ItemType": "Indicator",
                "LowerGoalpost": 0.0,
                "Policy": "Endangered Species Protection",
                "SourceOrganization": "UN SDG",
                "SourceOrganizationIndicatorCode": "[\"15.5.1\"]",
                "SourceOrganizationURL": "https://unstats.un.org/sdgapi/swagger/",
                "TreePath": "sspi/sus/eco/redlst",
                "UpperGoalpost": 1.0
            }
        },
        {
            "DocumentType": "CategoryDetail",
            "Metadata": {
                "Category": "Ecosystem",
                "CategoryCode": "ECO",
                "Children": [
                    "BIODIV",
                    "REDLST"
                ],
                "Description": "Placeholder",
                "DocumentType": "CategoryDetail",
                "IndicatorCodes": [
                    "BIODIV",
                    "REDLST"
                ],
                "ItemCode": "ECO",
                "ItemName": "Ecosystem",
                "ItemOrder": 0,
                "ItemType": "Category",
                "Pillar": "Sustainability",
                "PillarCode": "SUS",
                "ShortDescription": "Policies protecting natural ecosystems",
                "TreePath": "sspi/sus/eco"
            }
        },
        {
            "DocumentType": "PillarDetail",
            "Metadata": {
                "CategoryCodes": [
                    "ECO"
                ],
                "Children": [
                    "ECO"
                ],
                "Description": "Placeholder",
                "DocumentType": "PillarDetail",
                "ItemCode": "SUS",
                "ItemName": "Sustainability",
                "ItemOrder": 0,
                "ItemType": "Pillar",
                "Pillar": "Sustainability",
                "PillarCode": "SUS",
                "ShortDescription": "Measures policies protecting ecosystems and the environment.",
                "TreePath": "sspi/sus"
            }
        },
        {
            "DocumentType": "SSPIDetail",
            "Metadata": {
                "Children": [
                    "SUS"
                ],
                "Code": "SSPI",
                "Description": "The Sustainable and Shared Proseperity Index scores national policies across three pillars: Sustainability, Market Structure, and Public Goods\n",
                "DocumentType": "SSPIDetail",
                "ItemCode": "SSPI",
                "ItemName": "Sustainable and Shared Prosperity Policy Index",
                "ItemOrder": 0,
                "ItemType": "SSPI",
                "Name": "Sustainable and Shared Prosperity Policy Index",
                "PillarCodes": [
                    "SUS",
                ],
                "ShortDescription": "The Sustainable and Shared Proseperity Index scores national policies across three pillars: Sustainability, Market Structure, and Public Goods\n",
                "TreePath": "sspi"
            }
        },

        {
            "DocumentType": "DatasetCodes",
            "Metadata": ["UNSDG_MARINE", "UNSDG_TERRST", "UNSDG_FRSHWT", "UNSDG_REDLST"]
        },
        {   
            "DocumentType": "IndicatorCodes", 
            "Metadata": ["BIODIV", "REDLST"]
        },
        {
            "DocumentType": "PillarCodes",
            "Metadata": ["SUS"]
        },
        {
            "DocumentType": "CategoryCodes",
            "Metadata": ["ECO"]
        }
    ])
    yield sspi_metadata 
    sspi_metadata.delete_many({})
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)

def test_get_dataset_dependencies_dataset(sspi_metadata):
    dependencies = sspi_metadata.get_dataset_dependencies("UNSDG_MARINE")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 1
    dependencies = sspi_metadata.get_dataset_dependencies("UNSDG_TERRST")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 1
    dependencies = sspi_metadata.get_dataset_dependencies("UNSDG_FRSHWT")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 1
    dependencies = sspi_metadata.get_dataset_dependencies("UNSDG_REDLST")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 1

def test_get_dataset_dependencies_indicator(sspi_metadata):
    dependencies = sspi_metadata.get_dataset_dependencies("BIODIV")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 3
    assert "UNSDG_MARINE" in dependencies
    assert "UNSDG_TERRST" in dependencies
    assert "UNSDG_FRSHWT" in dependencies
    dependencies = sspi_metadata.get_dataset_dependencies("REDLST")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 1
    assert "UNSDG_REDLST" in dependencies

def test_get_dataset_dependencies_category(sspi_metadata):
    dependencies = sspi_metadata.get_dataset_dependencies("ECO")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 4
    assert "UNSDG_MARINE" in dependencies
    assert "UNSDG_TERRST" in dependencies
    assert "UNSDG_FRSHWT" in dependencies
    assert "UNSDG_REDLST" in dependencies

def test_get_dataset_dependencies_pillar(sspi_metadata):
    dependencies = sspi_metadata.get_dataset_dependencies("SUS")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 4
    assert "UNSDG_MARINE" in dependencies
    assert "UNSDG_TERRST" in dependencies
    assert "UNSDG_FRSHWT" in dependencies
    assert "UNSDG_REDLST" in dependencies

def test_get_dataset_dependencies_sspi(sspi_metadata):
    dependencies = sspi_metadata.get_dataset_dependencies("SSPI")
    assert isinstance(dependencies, list)
    assert len(dependencies) == 4
    assert "UNSDG_MARINE" in dependencies
    assert "UNSDG_TERRST" in dependencies
    assert "UNSDG_FRSHWT" in dependencies
    assert "UNSDG_REDLST" in dependencies
