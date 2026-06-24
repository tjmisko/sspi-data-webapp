"""
Integration tests for Weight persistence round-trip (F1).

Proves the optional per-child Weight field survives save -> load -> export
unchanged, both at the model layer (SSPICustomUserStructure) and through the
HTTP routes (/save, /load, /export).

NOTE: needs a live MongoDB. These tests WRITE to the real
sspi_custom_user_structure collection under a unique throwaway username and
clean up after themselves (function-scoped fixtures). Run with the dev Mongo
up:

    pytest tests/integration/test_weight_round_trip.py -v
"""
import json

import pytest
from unittest.mock import patch
from flask_bcrypt import Bcrypt

from sspi_flask_app.models.database import sspi_custom_user_structure, sspidb
from sspi_flask_app.models.usermodel import User


WEIGHT_RT_USERNAME = "weight_rt_user"


def _weighted_metadata():
    """A small valid structure carrying explicit per-parent weights."""
    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1"], "PillarCodes": ["PILLR1"]},
        {"ItemType": "Pillar", "ItemCode": "PILLR1", "ItemName": "P1",
         "PillarCode": "PILLR1", "Children": ["CATG01"],
         "CategoryCodes": ["CATG01"], "Weight": 1.0},
        {"ItemType": "Category", "ItemCode": "CATG01", "ItemName": "C1",
         "CategoryCode": "CATG01", "PillarCode": "PILLR1",
         "Children": ["INDIC1", "INDIC2"],
         "IndicatorCodes": ["INDIC1", "INDIC2"], "Weight": 1.0},
        {"ItemType": "Indicator", "ItemCode": "INDIC1", "ItemName": "I1",
         "IndicatorCode": "INDIC1", "DatasetCodes": ["DS_ONE"],
         "ScoreFunction": "Score = goalpost(DS_ONE, 0, 100)", "Children": [],
         "Weight": 0.75},
        {"ItemType": "Indicator", "ItemCode": "INDIC2", "ItemName": "I2",
         "IndicatorCode": "INDIC2", "DatasetCodes": ["DS_TWO"],
         "ScoreFunction": "Score = goalpost(DS_TWO, 0, 100)", "Children": [],
         "Weight": 0.25},
    ]


def _weight_of(metadata, item_code):
    for item in metadata:
        if item.get("ItemCode") == item_code:
            return item.get("Weight")
    raise AssertionError(f"{item_code} not in metadata")


# =============================================================================
# Model-layer round-trip
# =============================================================================

@pytest.fixture(scope="function")
def cleanup_rt_user():
    """Remove any configs owned by the throwaway round-trip user."""
    sspi_custom_user_structure.delete_many({"username": WEIGHT_RT_USERNAME})
    yield
    sspi_custom_user_structure.delete_many({"username": WEIGHT_RT_USERNAME})


class TestModelLayerWeightRoundTrip:
    def test_create_then_load_preserves_weights(self, app, cleanup_rt_user):
        config_id = sspi_custom_user_structure.create_config(
            name="weights-rt",
            metadata=_weighted_metadata(),
            username=WEIGHT_RT_USERNAME,
        )
        loaded = sspi_custom_user_structure.find_by_config_id(
            config_id, username=WEIGHT_RT_USERNAME
        )
        meta = loaded["metadata"]
        assert _weight_of(meta, "PILLR1") == 1.0
        assert _weight_of(meta, "INDIC1") == 0.75
        assert _weight_of(meta, "INDIC2") == 0.25

    def test_weightless_items_have_no_injected_weight(self, app, cleanup_rt_user):
        config_id = sspi_custom_user_structure.create_config(
            name="weights-rt-partial",
            metadata=_weighted_metadata(),
            username=WEIGHT_RT_USERNAME,
        )
        loaded = sspi_custom_user_structure.find_by_config_id(
            config_id, username=WEIGHT_RT_USERNAME
        )
        # SSPI root was never weighted -> no Weight key injected.
        sspi_item = next(m for m in loaded["metadata"] if m["ItemType"] == "SSPI")
        assert "Weight" not in sspi_item

    def test_update_changes_weight(self, app, cleanup_rt_user):
        config_id = sspi_custom_user_structure.create_config(
            name="weights-rt-update",
            metadata=_weighted_metadata(),
            username=WEIGHT_RT_USERNAME,
        )
        updated = _weighted_metadata()
        for item in updated:
            if item["ItemCode"] == "INDIC1":
                item["Weight"] = 0.6
            if item["ItemCode"] == "INDIC2":
                item["Weight"] = 0.4
        ok = sspi_custom_user_structure.update_config(
            config_id, WEIGHT_RT_USERNAME, {"metadata": updated}
        )
        assert ok
        loaded = sspi_custom_user_structure.find_by_config_id(
            config_id, username=WEIGHT_RT_USERNAME
        )
        assert _weight_of(loaded["metadata"], "INDIC1") == 0.6
        assert _weight_of(loaded["metadata"], "INDIC2") == 0.4

    def test_duplicate_carries_weights(self, app, cleanup_rt_user):
        config_id = sspi_custom_user_structure.create_config(
            name="weights-rt-dup",
            metadata=_weighted_metadata(),
            username=WEIGHT_RT_USERNAME,
        )
        dup_id = sspi_custom_user_structure.duplicate_config(
            config_id, WEIGHT_RT_USERNAME, "weights-rt-dup-copy"
        )
        dup = sspi_custom_user_structure.find_by_config_id(
            dup_id, username=WEIGHT_RT_USERNAME
        )
        assert _weight_of(dup["metadata"], "INDIC1") == 0.75
        assert _weight_of(dup["metadata"], "INDIC2") == 0.25

    def test_bad_weight_is_rejected_on_create(self, app, cleanup_rt_user):
        from sspi_flask_app.models.errors import InvalidDocumentFormatError
        bad = _weighted_metadata()
        bad[1]["Weight"] = 1.5  # out of range
        with pytest.raises(InvalidDocumentFormatError):
            sspi_custom_user_structure.create_config(
                name="weights-rt-bad", metadata=bad, username=WEIGHT_RT_USERNAME
            )


# =============================================================================
# Route-layer round-trip (/save -> /load -> /export)
# =============================================================================

@pytest.fixture(scope="function")
def rt_auth_db():
    test_db = sspidb.test_weight_rt_users
    test_db.delete_many({})
    yield test_db
    test_db.delete_many({})
    sspidb.drop_collection(test_db)


@pytest.fixture(scope="function")
def rt_user(rt_auth_db):
    """Create a regular user backed by a throwaway user collection."""
    with patch('sspi_flask_app.models.usermodel.sspi_user_data') as mock_user_data, \
         patch('sspi_flask_app.auth.routes.sspi_user_data') as mock_auth_routes:
        from sspi_flask_app.models.database.sspi_user_data import SSPIUserData
        wrapper = SSPIUserData(rt_auth_db)
        for mock in (mock_user_data, mock_auth_routes):
            mock.find_by_username = wrapper.find_by_username
            mock.find_by_api_key = wrapper.find_by_api_key
            mock.find_by_id = wrapper.find_by_id
            mock.create_user = wrapper.create_user
            mock.username_exists = wrapper.username_exists
            mock.get_user_roles = wrapper.get_user_roles

        bcrypt = Bcrypt()
        password_hash = bcrypt.generate_password_hash("pw123456").decode("utf-8")
        user = User.create_user(WEIGHT_RT_USERNAME, password_hash, roles=["user"])
        # Clean any prior configs for this username before/after.
        sspi_custom_user_structure.delete_many({"username": WEIGHT_RT_USERNAME})
        yield {"username": WEIGHT_RT_USERNAME, "apikey": user.apikey}
        sspi_custom_user_structure.delete_many({"username": WEIGHT_RT_USERNAME})


class TestRouteLayerWeightRoundTrip:
    def test_save_load_export_round_trip(self, app, client, rt_user):
        headers = {"Authorization": f"Bearer {rt_user['apikey']}"}

        # /save
        save = client.post(
            "/api/v1/customize/save",
            json={"name": "weights-route-rt", "metadata": _weighted_metadata()},
            headers=headers,
        )
        assert save.status_code == 200, save.get_data(as_text=True)
        config_id = save.get_json()["config_id"]

        # /load -> weights repopulated
        load = client.get(f"/api/v1/customize/load/{config_id}", headers=headers)
        assert load.status_code == 200
        meta = load.get_json()["metadata"]
        assert _weight_of(meta, "PILLR1") == 1.0
        assert _weight_of(meta, "INDIC1") == 0.75
        assert _weight_of(meta, "INDIC2") == 0.25

        # /export -> weights present in the downloadable JSON
        export = client.get(f"/api/v1/customize/export/{config_id}", headers=headers)
        assert export.status_code == 200
        payload = json.loads(export.get_data(as_text=True))
        export_meta = payload["configuration"]["metadata"]
        assert _weight_of(export_meta, "INDIC1") == 0.75
        assert _weight_of(export_meta, "INDIC2") == 0.25
