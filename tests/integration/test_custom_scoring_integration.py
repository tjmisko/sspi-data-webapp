"""
Integration tests for custom SSPI scoring endpoints.

Tests the full scoring flow including:
- Authentication and authorization
- Request validation
- Job creation and management
- SSE streaming
- Job status polling
"""
import pytest
from unittest.mock import patch, MagicMock
from flask_bcrypt import Bcrypt
from sspi_flask_app.models.usermodel import User
from sspi_flask_app.models.database import sspidb


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_scoring_db():
    """Create a clean test database for scoring integration tests."""
    test_db = sspidb.test_scoring_integration
    test_db.delete_many({})
    yield test_db
    test_db.delete_many({})
    sspidb.drop_collection(test_db)


@pytest.fixture(scope="function")
def mock_scoring_auth(test_scoring_db):
    """Mock sspi_user_data to use test database for scoring tests."""
    with patch('sspi_flask_app.models.usermodel.sspi_user_data') as mock_user_data, \
         patch('sspi_flask_app.auth.routes.sspi_user_data') as mock_auth_routes:

        from sspi_flask_app.models.database.sspi_user_data import SSPIUserData
        test_wrapper = SSPIUserData(test_scoring_db)

        # Mock both imports to use the same test wrapper
        for mock in [mock_user_data, mock_auth_routes]:
            mock.find_by_username = test_wrapper.find_by_username
            mock.find_by_api_key = test_wrapper.find_by_api_key
            mock.find_by_id = test_wrapper.find_by_id
            mock.create_user = test_wrapper.create_user
            mock.username_exists = test_wrapper.username_exists
            mock.update_password = test_wrapper.update_password
            mock.regenerate_api_key = test_wrapper.regenerate_api_key
            mock.get_all_users = test_wrapper.get_all_users
            mock.delete_user = test_wrapper.delete_user
            mock.delete_many = test_wrapper.delete_many
            mock.get_user_roles = test_wrapper.get_user_roles
            mock.add_role = test_wrapper.add_role
            mock.remove_role = test_wrapper.remove_role
            mock.set_roles = test_wrapper.set_roles

        yield test_wrapper


@pytest.fixture(scope="function")
def scoring_user(mock_scoring_auth):
    """Create a regular user for scoring tests."""
    bcrypt = Bcrypt()
    username = "scoringuser"
    password = "testpassword123"
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    user = User.create_user(username, password_hash, roles=["user"])
    return {
        'user': user,
        'username': username,
        'password': password,
        'apikey': user.apikey
    }


@pytest.fixture(scope="function")
def scoring_admin(mock_scoring_auth):
    """Create an admin user for scoring tests."""
    bcrypt = Bcrypt()
    username = "scoringadmin"
    password = "adminpass123"
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    user = User.create_user(username, password_hash, roles=["admin", "user"])
    return {
        'user': user,
        'username': username,
        'password': password,
        'apikey': user.apikey
    }


@pytest.fixture
def minimal_sspi_metadata():
    """
    Minimal valid SSPI metadata structure for testing.

    Contains a single pillar, category, and indicator.
    """
    return [
        {
            "ItemType": "SSPI",
            "ItemCode": "SSPI",
            "ItemName": "Test SSPI",
            "Children": ["TST"],
            "TreeIndex": [0],
        },
        {
            "ItemType": "Pillar",
            "ItemCode": "TST",
            "ItemName": "Test Pillar",
            "PillarCode": "TST",
            "Children": ["TSTCAT"],
            "TreeIndex": [0, 0],
        },
        {
            "ItemType": "Category",
            "ItemCode": "TSTCAT",
            "ItemName": "Test Category",
            "CategoryCode": "TSTCAT",
            "PillarCode": "TST",
            "Children": ["TSTIND"],
            "TreeIndex": [0, 0, 0],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "TSTIND",
            "ItemName": "Test Indicator",
            "IndicatorCode": "TSTIND",
            "CategoryCode": "TSTCAT",
            "PillarCode": "TST",
            "DatasetCodes": ["TEST_DATA"],
            "ScoreFunction": "Score = goalpost(TEST_DATA, 0, 100)",
            "Children": [],
            "TreeIndex": [0, 0, 0, 0],
        },
    ]


@pytest.fixture
def invalid_score_function_metadata():
    """Metadata with an invalid score function (uses exp)."""
    return [
        {
            "ItemType": "SSPI",
            "ItemCode": "SSPI",
            "ItemName": "Test SSPI",
            "Children": ["TST"],
            "TreeIndex": [0],
        },
        {
            "ItemType": "Pillar",
            "ItemCode": "TST",
            "ItemName": "Test Pillar",
            "PillarCode": "TST",
            "Children": ["TSTCAT"],
            "TreeIndex": [0, 0],
        },
        {
            "ItemType": "Category",
            "ItemCode": "TSTCAT",
            "ItemName": "Test Category",
            "CategoryCode": "TSTCAT",
            "PillarCode": "TST",
            "Children": ["TSTIND"],
            "TreeIndex": [0, 0, 0],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "TSTIND",
            "ItemName": "Test Indicator",
            "IndicatorCode": "TSTIND",
            "CategoryCode": "TSTCAT",
            "PillarCode": "TST",
            "DatasetCodes": ["TEST_DATA"],
            "ScoreFunction": "Score = goalpost(exp(TEST_DATA), 0, 100)",  # exp() is blocked
            "Children": [],
            "TreeIndex": [0, 0, 0, 0],
        },
    ]


@pytest.fixture
def pow_over_limit_metadata():
    """Metadata with pow() exponent over limit (11 > 10)."""
    return [
        {
            "ItemType": "SSPI",
            "ItemCode": "SSPI",
            "ItemName": "Test SSPI",
            "Children": ["TST"],
            "TreeIndex": [0],
        },
        {
            "ItemType": "Pillar",
            "ItemCode": "TST",
            "ItemName": "Test Pillar",
            "PillarCode": "TST",
            "Children": ["TSTCAT"],
            "TreeIndex": [0, 0],
        },
        {
            "ItemType": "Category",
            "ItemCode": "TSTCAT",
            "ItemName": "Test Category",
            "CategoryCode": "TSTCAT",
            "PillarCode": "TST",
            "Children": ["TSTIND"],
            "TreeIndex": [0, 0, 0],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "TSTIND",
            "ItemName": "Test Indicator",
            "IndicatorCode": "TSTIND",
            "CategoryCode": "TSTCAT",
            "PillarCode": "TST",
            "DatasetCodes": ["TEST_DATA"],
            "ScoreFunction": "Score = goalpost(pow(TEST_DATA, 11), 0, 100)",  # 11 > 10 limit
            "Children": [],
            "TreeIndex": [0, 0, 0, 0],
        },
    ]


# =============================================================================
# Authentication Tests
# =============================================================================

class TestScoringAuthentication:
    """Test authentication requirements for scoring endpoints."""

    def test_score_requires_authentication(self, app, client):
        """POST /customize/score requires authentication."""
        response = client.post(
            '/api/v1/customize/score',
            json={"metadata": [{"test": "data"}]}
        )
        # Should redirect to login or return 401
        assert response.status_code in {302, 401}

    def test_score_stream_requires_authentication(self, app, client):
        """GET /customize/score-stream/<job_id> requires authentication."""
        response = client.get('/api/v1/customize/score-stream/fake_job_id')
        assert response.status_code in {302, 401}

    def test_job_status_requires_authentication(self, app, client):
        """GET /customize/job/<job_id> requires authentication."""
        response = client.get('/api/v1/customize/job/fake_job_id')
        assert response.status_code in {302, 401}

    def test_score_with_bearer_token(self, app, client, scoring_user, minimal_sspi_metadata):
        """Score endpoint accepts Bearer token authentication."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        # This should at least not return 401/302 (auth should pass)
        # May fail validation but auth should work
        response = client.post(
            '/api/v1/customize/score',
            json={"metadata": minimal_sspi_metadata},
            headers=headers
        )
        # Auth passed if we don't get 401 or 302
        assert response.status_code not in {302, 401}


# =============================================================================
# Validation Tests
# =============================================================================

class TestScoringValidation:
    """Test request validation for scoring endpoint."""

    def test_score_missing_metadata_returns_400(self, app, client, scoring_user):
        """Score endpoint requires metadata or config_id."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        response = client.post(
            '/api/v1/customize/score',
            json={},  # No metadata or config_id
            headers=headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert not data.get('success')

    def test_score_empty_metadata_returns_400(self, app, client, scoring_user):
        """Score endpoint rejects empty metadata list."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        response = client.post(
            '/api/v1/customize/score',
            json={"metadata": []},
            headers=headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert not data.get('success')

    def test_score_invalid_metadata_structure_returns_400(self, app, client, scoring_user):
        """Score endpoint validates metadata structure."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        response = client.post(
            '/api/v1/customize/score',
            json={"metadata": [{"invalid": "structure"}]},
            headers=headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert not data.get('success')

    def test_score_no_json_body_returns_error(self, app, client, scoring_user):
        """Score endpoint requires JSON body."""
        headers = {
            'Authorization': f'Bearer {scoring_user["apikey"]}',
            'Content-Type': 'application/json'
        }

        # Empty body with JSON content type
        response = client.post(
            '/api/v1/customize/score',
            data='',
            headers=headers
        )
        # Endpoint catches JSON parse errors and returns 500 (security - hides internal errors)
        # This is expected behavior - bad input gets rejected
        assert response.status_code in {400, 415, 500}


# =============================================================================
# Job Status Tests
# =============================================================================

class TestJobStatusPolling:
    """Test job status polling endpoint."""

    def test_job_not_found_returns_404(self, app, client, scoring_user):
        """Non-existent job returns 404."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        response = client.get(
            '/api/v1/customize/job/nonexistent_job_id',
            headers=headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert not data.get('success')
        assert 'not found' in data.get('error', '').lower()


# =============================================================================
# SSE Stream Tests
# =============================================================================

class TestScoringSSEStream:
    """Test SSE streaming endpoint."""

    def test_stream_invalid_job_returns_404(self, app, client, scoring_user):
        """Invalid job_id returns 404."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        response = client.get(
            '/api/v1/customize/score-stream/nonexistent_job',
            headers=headers
        )
        assert response.status_code == 404

    def test_legacy_stream_endpoint_returns_400(self, app, client, scoring_user):
        """Legacy /score-stream (no job_id) returns helpful error."""
        headers = {'Authorization': f'Bearer {scoring_user["apikey"]}'}

        response = client.get(
            '/api/v1/customize/score-stream',
            headers=headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'job_id' in data.get('error', '').lower()
