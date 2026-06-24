"""
Integration tests for the weight feature flag + /validate wiring (F3).

Covers:
- app.config["CUSTOM_WEIGHTS_ENABLED"] defaults to False.
- GET /api/v1/customize/weights-config reflects the flag (public, no auth).
- POST /api/v1/customize/validate now runs the real validator and returns
  structured weight errors (no more always-valid stub).

NOTE: needs a live MongoDB (the app/session fixtures connect on import). The
/validate route itself performs no Mongo writes; the authenticated tests use a
throwaway user collection that is cleaned up.

    pytest tests/integration/test_weight_validation_routes.py -v
"""
import pytest
from unittest.mock import patch
from flask_bcrypt import Bcrypt

from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.usermodel import User


def _valid_tree(weights=None):
    weights = weights or {}

    def w(item):
        if item["ItemCode"] in weights:
            return dict(item, Weight=weights[item["ItemCode"]])
        return item

    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1"], "PillarCodes": ["PILLR1"]},
        w({"ItemType": "Pillar", "ItemCode": "PILLR1", "ItemName": "P1",
           "PillarCode": "PILLR1", "Children": ["CATG01"],
           "CategoryCodes": ["CATG01"]}),
        {"ItemType": "Category", "ItemCode": "CATG01", "ItemName": "C1",
         "CategoryCode": "CATG01", "PillarCode": "PILLR1",
         "Children": ["INDIC1", "INDIC2"],
         "IndicatorCodes": ["INDIC1", "INDIC2"]},
        w({"ItemType": "Indicator", "ItemCode": "INDIC1", "ItemName": "I1",
           "IndicatorCode": "INDIC1", "Children": []}),
        w({"ItemType": "Indicator", "ItemCode": "INDIC2", "ItemName": "I2",
           "IndicatorCode": "INDIC2", "Children": []}),
    ]


# =============================================================================
# Feature flag
# =============================================================================

def test_flag_defaults_false(app):
    assert app.config.get("CUSTOM_WEIGHTS_ENABLED") is False


def test_weights_config_endpoint_reflects_flag(app, client):
    resp = client.get("/api/v1/customize/weights-config")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["custom_weights_enabled"] == bool(
        app.config.get("CUSTOM_WEIGHTS_ENABLED", False)
    )


# =============================================================================
# /validate wiring
# =============================================================================

@pytest.fixture(scope="function")
def validate_auth_db():
    test_db = sspidb.test_weight_validate_users
    test_db.delete_many({})
    yield test_db
    test_db.delete_many({})
    sspidb.drop_collection(test_db)


@pytest.fixture(scope="function")
def validate_user(validate_auth_db):
    with patch('sspi_flask_app.models.usermodel.sspi_user_data') as mock_user_data, \
         patch('sspi_flask_app.auth.routes.sspi_user_data') as mock_auth_routes:
        from sspi_flask_app.models.database.sspi_user_data import SSPIUserData
        wrapper = SSPIUserData(validate_auth_db)
        for mock in (mock_user_data, mock_auth_routes):
            mock.find_by_username = wrapper.find_by_username
            mock.find_by_api_key = wrapper.find_by_api_key
            mock.find_by_id = wrapper.find_by_id
            mock.create_user = wrapper.create_user
            mock.username_exists = wrapper.username_exists
            mock.get_user_roles = wrapper.get_user_roles
        bcrypt = Bcrypt()
        pw = bcrypt.generate_password_hash("pw123456").decode("utf-8")
        user = User.create_user("weight_validate_user", pw, roles=["user"])
        yield {"apikey": user.apikey}


class TestValidateRoute:
    def test_valid_weighted_config_passes(self, app, client, validate_user):
        headers = {"Authorization": f"Bearer {validate_user['apikey']}"}
        resp = client.post(
            "/api/v1/customize/validate",
            json={"metadata": _valid_tree({"INDIC1": 0.6, "INDIC2": 0.4})},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["valid"] is True
        weight_errors = [e for e in data["errors"] if e.get("field") == "Weight"]
        assert weight_errors == []

    def test_bad_weight_sum_is_rejected(self, app, client, validate_user):
        headers = {"Authorization": f"Bearer {validate_user['apikey']}"}
        resp = client.post(
            "/api/v1/customize/validate",
            json={"metadata": _valid_tree({"INDIC1": 0.6, "INDIC2": 0.6})},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["valid"] is False
        assert any(e.get("field") == "Weight" for e in data["errors"])

    def test_mixed_weights_rejected(self, app, client, validate_user):
        headers = {"Authorization": f"Bearer {validate_user['apikey']}"}
        resp = client.post(
            "/api/v1/customize/validate",
            json={"metadata": _valid_tree({"INDIC1": 1.0})},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["valid"] is False

    def test_validate_no_longer_always_valid(self, app, client, validate_user):
        # A structurally broken config must now report errors (the old stub
        # always returned valid: True).
        headers = {"Authorization": f"Bearer {validate_user['apikey']}"}
        resp = client.post(
            "/api/v1/customize/validate",
            json={"metadata": [{"ItemType": "Indicator", "ItemCode": "X"}]},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["valid"] is False
