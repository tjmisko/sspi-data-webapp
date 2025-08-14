import pytest
from sspi_flask_app.models.database.sspi_item_data import SSPIItemData
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture(scope="function")
def test_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    yield sspi_test_db
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)


@pytest.fixture(scope="function")
def sspi_item_data_wrapper(test_db):
    wrapper = SSPIItemData(test_db)
    yield wrapper


@pytest.fixture(scope="session")
def real_item_data_structure():
    """Sample data matching the actual structure in sspi_item_data"""
    return [
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SSPI",
            "ItemType": "SSPI",
            "Score": 0.8
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SUS",
            "ItemType": "Pillar",
            "Score": 0.85
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "BIODIV",
            "ItemType": "Indicator",
            "Score": 0.90
        }
    ]


@pytest.fixture(scope="session")
def sample_hierarchical_data():
    """Sample item data with hierarchical structure that active_schema expects"""
    return [
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SSPI",
            "ItemName": "Social Progress Index",
            "Score": 0.8,
            "Children": ["SUS", "MS", "PG"]
        },
        {
            "CountryCode": "USA", 
            "Year": 2018,
            "ItemCode": "SUS",
            "ItemName": "Sustainability",
            "Score": 0.85,
            "Children": ["ECO", "LND"]
        },
        {
            "CountryCode": "USA",
            "Year": 2018, 
            "ItemCode": "MS",
            "ItemName": "Market Structure",
            "Score": 0.75,
            "Children": ["COMP", "BANK"]
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "PG", 
            "ItemName": "Public Goods",
            "Score": 0.82,
            "Children": ["EDUC", "HLTH"]
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "ECO",
            "ItemName": "Ecosystem",
            "Score": 0.9,
            "Children": ["BIODIV", "REDLST"]
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "LND", 
            "ItemName": "Land",
            "Score": 0.8,
            "Children": ["NITROG", "CARBON"]
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "BIODIV",
            "ItemName": "Biodiversity Protection",
            "Score": 0.95,
            "Children": []
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "REDLST",
            "ItemName": "Red List Index",
            "Score": 0.85,
            "Children": []
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "NITROG",
            "ItemName": "Nitrogen Use",
            "Score": 0.78,
            "Children": []
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "CARBON",
            "ItemName": "Carbon Pricing",
            "Score": 0.82,
            "Children": []
        }
    ]


def test_validate_document_format_valid(real_item_data_structure, sspi_item_data_wrapper):
    """Test that valid documents pass validation"""
    valid_doc = real_item_data_structure[0]
    sspi_item_data_wrapper.validate_document_format(valid_doc, 0)


def test_validate_document_format_missing_country_code(sspi_item_data_wrapper):
    """Test that missing CountryCode raises error"""
    invalid_doc = {
        "Year": 2018,
        "ItemCode": "SSPI",
        "Score": 0.8
    }
    with pytest.raises(InvalidDocumentFormatError) as exc_info:
        sspi_item_data_wrapper.validate_document_format(invalid_doc, 0)
    assert "CountryCode" in str(exc_info.value)


def test_validate_document_format_missing_item_code(sspi_item_data_wrapper):
    """Test that missing ItemCode raises error"""
    invalid_doc = {
        "CountryCode": "USA",
        "Year": 2018,
        "Score": 0.8
    }
    with pytest.raises(InvalidDocumentFormatError) as exc_info:
        sspi_item_data_wrapper.validate_document_format(invalid_doc, 0)
    assert "ItemCode" in str(exc_info.value)


def test_validate_document_format_missing_year(sspi_item_data_wrapper):
    """Test that missing Year raises error"""
    invalid_doc = {
        "CountryCode": "USA",
        "ItemCode": "SSPI",
        "Score": 0.8
    }
    with pytest.raises(InvalidDocumentFormatError) as exc_info:
        sspi_item_data_wrapper.validate_document_format(invalid_doc, 0)
    assert "Year" in str(exc_info.value)


def test_validate_document_format_missing_score(sspi_item_data_wrapper):
    """Test that missing Score raises error"""
    invalid_doc = {
        "CountryCode": "USA",
        "ItemCode": "SSPI",
        "Year": 2018
    }
    with pytest.raises(InvalidDocumentFormatError) as exc_info:
        sspi_item_data_wrapper.validate_document_format(invalid_doc, 0)
    assert "Score" in str(exc_info.value)


def test_active_schema_basic_structure(sample_hierarchical_data, sspi_item_data_wrapper):
    """Test that active_schema returns correct hierarchical structure"""
    sspi_item_data_wrapper.insert_many(sample_hierarchical_data)
    
    name_map = {
        "BIODIV": "Biodiversity Protection Indicator",
        "REDLST": "Red List Indicator"
    }
    
    schema = sspi_item_data_wrapper.active_schema(
        sample_country="USA", 
        sample_year=2018, 
        name_map=name_map
    )
    
    assert schema is not None
    assert schema["ItemCode"] == "SSPI"
    assert schema["ItemName"] == "Social Progress Index"
    assert len(schema["Children"]) == 1  # Only SUS has children with data
    
    pillar_codes = [child["ItemCode"] for child in schema["Children"]]
    assert "SUS" in pillar_codes
    # MS and PG are excluded because they have no children with data


def test_active_schema_deep_hierarchy(sample_hierarchical_data, sspi_item_data_wrapper):
    """Test that active_schema builds deep hierarchical structures correctly"""
    sspi_item_data_wrapper.insert_many(sample_hierarchical_data)
    
    schema = sspi_item_data_wrapper.active_schema(sample_country="USA", sample_year=2018)
    
    pillar = schema["Children"][0]  # SUS
    assert pillar["ItemCode"] == "SUS"
    assert pillar["ItemName"] == "Sustainability"
    assert len(pillar["Children"]) == 2
    
    category = pillar["Children"][0]  # ECO
    assert category["ItemCode"] == "ECO"
    assert category["ItemName"] == "Ecosystem"
    assert len(category["Children"]) == 2
    
    indicator = category["Children"][0]  # BIODIV
    assert indicator["ItemCode"] == "BIODIV"
    assert indicator["ItemName"] == "Biodiversity Protection"
    assert len(indicator["Children"]) == 0


def test_active_schema_with_name_map(sample_hierarchical_data, sspi_item_data_wrapper):
    """Test that active_schema uses name_map when ItemName is missing"""
    # Remove ItemName from BIODIV to test name_map fallback
    modified_data = []
    for item in sample_hierarchical_data:
        if item["ItemCode"] == "BIODIV":
            item_copy = item.copy()
            del item_copy["ItemName"]
            modified_data.append(item_copy)
        else:
            modified_data.append(item)
    
    sspi_item_data_wrapper.insert_many(modified_data)
    
    name_map = {
        "BIODIV": "Custom Biodiversity Name",
        "REDLST": "Custom Red List Name"
    }
    
    schema = sspi_item_data_wrapper.active_schema(
        sample_country="USA", 
        sample_year=2018, 
        name_map=name_map
    )
    
    pillar = schema["Children"][0]
    category = pillar["Children"][0]
    indicator = category["Children"][0]
    
    # Should use name_map since ItemName was removed
    assert indicator["ItemName"] == "Custom Biodiversity Name"


def test_active_schema_no_data_raises_error(sspi_item_data_wrapper):
    """Test that active_schema raises ValueError when no data found"""
    with pytest.raises(ValueError) as exc_info:
        sspi_item_data_wrapper.active_schema(sample_country="XXX", sample_year=2020)
    
    assert "No data found for country XXX in year 2020" in str(exc_info.value)


def test_active_schema_missing_children_field(sspi_item_data_wrapper):
    """Test that active_schema handles missing Children field gracefully"""
    incomplete_data = [
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SSPI",
            "ItemName": "Social Progress Index",
            "Score": 0.8
            # Missing Children field
        }
    ]
    
    sspi_item_data_wrapper.insert_many(incomplete_data)
    
    schema = sspi_item_data_wrapper.active_schema(sample_country="USA", sample_year=2018)
    
    # SSPI with no children returns None since there's no actual data to show
    assert schema is None


def test_active_schema_empty_children_list(sspi_item_data_wrapper):
    """Test that active_schema handles empty Children list"""
    data_with_empty_children = [
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SSPI",
            "ItemName": "Social Progress Index",
            "Score": 0.8,
            "Children": []
        }
    ]
    
    sspi_item_data_wrapper.insert_many(data_with_empty_children)
    
    schema = sspi_item_data_wrapper.active_schema(sample_country="USA", sample_year=2018)
    
    # SSPI with no children returns None since there's no actual data to show
    assert schema is None


def test_active_schema_missing_child_items(sample_hierarchical_data, sspi_item_data_wrapper):
    """Test that active_schema handles missing child items gracefully"""
    # Insert only SSPI and SUS, but SSPI references MS and PG which don't exist
    partial_data = [
        sample_hierarchical_data[0],  # SSPI
        sample_hierarchical_data[1],  # SUS
    ]
    
    sspi_item_data_wrapper.insert_many(partial_data)
    
    schema = sspi_item_data_wrapper.active_schema(sample_country="USA", sample_year=2018)
    
    # SSPI with only SUS (which has no children with scores) returns None
    assert schema is None


def test_active_schema_default_parameters(sample_hierarchical_data, sspi_item_data_wrapper):
    """Test active_schema with default parameters"""
    # Add data for USA 2018 (default values)
    sspi_item_data_wrapper.insert_many(sample_hierarchical_data)
    
    schema = sspi_item_data_wrapper.active_schema()
    
    assert schema is not None
    assert schema["ItemCode"] == "SSPI"


def test_active_schema_real_world_behavior(sspi_item_data_wrapper):
    """Test active_schema with structure that finalize function would create"""
    # This mimics what the finalize function creates - score documents with Children from metadata
    finalize_style_data = [
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SSPI",
            "ItemType": "SSPI",
            "Score": 0.8,
            "Children": ["SUS", "MS", "PG"],  # Added by finalize from metadata
            "ItemName": "Sustainable and Shared Prosperity Policy Index"
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "SUS",
            "ItemType": "Pillar",
            "Score": 0.85,
            "Children": ["ECO", "LND"],  # Added by finalize from metadata
            "ItemName": "Sustainability"
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "ECO",
            "ItemType": "Category",
            "Score": 0.9,
            "Children": ["BIODIV", "REDLST"],  # Added by finalize from metadata
            "ItemName": "Ecosystem"
        },
        {
            "CountryCode": "USA",
            "Year": 2018,
            "ItemCode": "BIODIV",
            "ItemType": "Indicator",
            "Score": 0.95,
            "Children": [],  # Indicators have no children
            "ItemName": "Biodiversity Protection"
        }
    ]
    
    sspi_item_data_wrapper.insert_many(finalize_style_data)
    
    schema = sspi_item_data_wrapper.active_schema(sample_country="USA", sample_year=2018)
    
    # Should build proper tree
    assert schema["ItemCode"] == "SSPI"
    assert schema["ItemName"] == "Sustainable and Shared Prosperity Policy Index"
    assert len(schema["Children"]) == 1  # Only existing children with data are included
    
    # Find SUS pillar which exists in data
    sus_pillar = next(child for child in schema["Children"] if child["ItemCode"] == "SUS")
    assert sus_pillar["ItemName"] == "Sustainability"
    assert len(sus_pillar["Children"]) == 1  # Only existing children with data are included
    
    # Find ECO category which exists in data  
    eco_category = next(child for child in sus_pillar["Children"] if child["ItemCode"] == "ECO")
    assert eco_category["ItemName"] == "Ecosystem"
    assert len(eco_category["Children"]) == 1  # Only existing children with data are included
    
    # Find BIODIV indicator which exists in data
    biodiv_indicator = next(child for child in eco_category["Children"] if child["ItemCode"] == "BIODIV")
    assert biodiv_indicator["ItemName"] == "Biodiversity Protection"
    assert len(biodiv_indicator["Children"]) == 0
    
    # REDLST should not be included since it doesn't exist in data