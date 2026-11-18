from unittest.mock import patch

from sspi_flask_app.api.core import customize
from sspi_flask_app.api.core.customize import build_dataset_details_map


TRNETW = {
    "ItemType": "Indicator",
    "ItemCode": "TRNETW",
    "DatasetCodes": ["WB_RAILNT", "CIA_ROADNT"],
}
CIA = {"DatasetCode": "CIA_ROADNT", "DatasetName": "Roadways"}


def test_should_keep_dataset_code_when_it_has_no_metadata():
    result = build_dataset_details_map([CIA], [TRNETW])
    assert list(result) == ["CIA_ROADNT", "WB_RAILNT"]
    assert result["WB_RAILNT"]["Unknown"] is True
    assert result["WB_RAILNT"]["DatasetCode"] == "WB_RAILNT"
    assert result["CIA_ROADNT"] is CIA


def test_should_not_override_real_metadata_when_code_is_known():
    result = build_dataset_details_map([CIA], [{"DatasetCodes": ["CIA_ROADNT"]}])
    assert result == {"CIA_ROADNT": CIA}


def test_should_ignore_malformed_items_when_building_map():
    items = [None, "x", {"DatasetCodes": "WB_X"}, {"DatasetCodes": [None, "", 5]}, {}]
    assert build_dataset_details_map([CIA], items) == {"CIA_ROADNT": CIA}
    assert build_dataset_details_map([CIA], None) == {"CIA_ROADNT": CIA}


def test_should_include_unknown_dataset_when_default_structure_requested(client):
    with patch.object(customize.sspi_metadata, "item_details", return_value=[dict(TRNETW)]), \
         patch.object(customize.sspi_metadata, "organization_details", return_value=[]), \
         patch.object(customize.sspi_metadata, "dataset_details", return_value=[dict(CIA)]):
        response = client.get("/api/v1/customize/default-structure")
    assert response.status_code == 200
    details = response.get_json()["datasetDetailsMap"]
    assert "WB_RAILNT" in details
    assert details["WB_RAILNT"]["Unknown"] is True
    assert "CIA_ROADNT" in details
