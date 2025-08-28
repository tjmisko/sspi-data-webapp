"""
Integration tests for MongoDB-based authentication system.

Tests the full authentication flow from User model through Flask routes.
"""
import pytest
from unittest.mock import patch
from flask import url_for
from flask_bcrypt import Bcrypt
from bs4 import BeautifulSoup
from sspi_flask_app.models.usermodel import User
from sspi_flask_app.models.database import sspidb


def get_csrf_token(client, url):
    """Helper to get CSRF token from a form page."""
    response = client.get(url)
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        return csrf_input.get('value')
    return None


@pytest.fixture(scope="function")
def test_auth_db():
    """Create a clean test database for auth integration tests."""
    test_db = sspidb.test_auth_integration
    test_db.delete_many({})
    yield test_db
    test_db.delete_many({})
    sspidb.drop_collection(test_db)


@pytest.fixture(scope="function")
def mock_auth_data(test_auth_db):
    """Mock sspi_user_data to use test database for auth routes."""
    with patch('sspi_flask_app.models.usermodel.sspi_user_data') as mock_user_data, \
         patch('sspi_flask_app.auth.routes.sspi_user_data') as mock_auth_routes:
        
        from sspi_flask_app.models.database.sspi_user_data import SSPIUserData
        test_wrapper = SSPIUserData(test_auth_db)
        
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
        
        yield test_wrapper


@pytest.fixture(scope="function")
def test_user(mock_auth_data):
    """Create a test user for authentication tests."""
    bcrypt = Bcrypt()
    username = "testuser"
    password = "testpassword123"
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    user = User.create_user(username, password_hash)
    return {
        'user': user,
        'username': username,
        'password': password,
        'password_hash': password_hash
    }


class TestAuthenticationIntegration:
    """Test full authentication integration."""
    
    def test_user_creation_and_retrieval(self, mock_auth_data):
        """Test creating user and retrieving by different methods."""
        bcrypt = Bcrypt()
        username = "integrationuser"
        password = "password123"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        user = User.create_user(username, password_hash)
        assert user is not None
        assert user.username == username
        
        # Find by username
        found_user = User.find_by_username(username)
        assert found_user is not None
        assert found_user.id == user.id
        
        # Find by API key
        api_user = User.find_by_api_key(user.apikey)
        assert api_user is not None
        assert api_user.id == user.id
        
        # Find by ID
        id_user = User.find_by_id(user.id)
        assert id_user is not None
        assert id_user.username == username
    
    def test_password_verification(self, mock_auth_data):
        """Test password hashing and verification."""
        bcrypt = Bcrypt()
        username = "passworduser"
        password = "securepassword123"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user = User.create_user(username, password_hash)
        
        # Verify correct password
        assert bcrypt.check_password_hash(user.password, password) is True
        
        # Verify incorrect password
        assert bcrypt.check_password_hash(user.password, "wrongpassword") is False
    
    def test_api_key_authentication(self, mock_auth_data):
        """Test API key-based authentication."""
        bcrypt = Bcrypt()
        username = "apiuser"
        password = "password123"
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user = User.create_user(username, password_hash)
        original_api_key = user.apikey
        
        # Find user by API key
        api_user = User.find_by_api_key(original_api_key)
        assert api_user is not None
        assert api_user.username == username
        
        # Regenerate API key
        new_api_key = user.regenerate_api_key()
        assert new_api_key != original_api_key
        assert len(new_api_key) == 128
        
        # Old API key should no longer work
        old_api_user = User.find_by_api_key(original_api_key)
        assert old_api_user is None
        
        # New API key should work
        new_api_user = User.find_by_api_key(new_api_key)
        assert new_api_user is not None
        assert new_api_user.id == user.id
    
    def test_user_management_operations(self, mock_auth_data):
        """Test user management operations."""
        bcrypt = Bcrypt()
        
        # Create multiple users
        users = []
        for i in range(3):
            username = f"user{i}"
            password_hash = bcrypt.generate_password_hash(f"password{i}").decode('utf-8')
            user = User.create_user(username, password_hash)
            users.append(user)
        
        # Get all users
        all_users = User.get_all_users()
        assert len(all_users) == 3
        usernames = [u.username for u in all_users]
        for user in users:
            assert user.username in usernames
        
        # Update password
        new_password_hash = bcrypt.generate_password_hash("newpassword").decode('utf-8')
        success = users[0].update_password(new_password_hash)
        assert success is True
        assert users[0].password == new_password_hash
        
        # Delete user
        success = users[0].delete()
        assert success is True
        
        # Verify user is deleted
        deleted_user = User.find_by_id(users[0].id)
        assert deleted_user is None
        
        # Remaining users should still exist
        remaining_users = User.get_all_users()
        assert len(remaining_users) == 2
    
    def test_duplicate_username_prevention(self, mock_auth_data):
        """Test that duplicate usernames are prevented."""
        bcrypt = Bcrypt()
        username = "duplicateuser"
        password_hash = bcrypt.generate_password_hash("password").decode('utf-8')
        
        # Create first user
        user1 = User.create_user(username, password_hash)
        assert user1 is not None
        
        # Try to create second user with same username
        from sspi_flask_app.models.errors import InvalidDocumentFormatError
        with pytest.raises(InvalidDocumentFormatError, match="already exists"):
            User.create_user(username, password_hash)
    
    def test_flask_login_integration(self, mock_auth_data):
        """Test Flask-Login integration properties."""
        bcrypt = Bcrypt()
        username = "flaskuser"
        password_hash = bcrypt.generate_password_hash("password").decode('utf-8')
        
        user = User.create_user(username, password_hash)
        
        # Test Flask-Login required properties
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False
        assert isinstance(user.get_id(), str)
        assert user.get_id() == user.id


class TestAuthenticationRouteIntegration:
    """Test authentication routes with MongoDB backend."""
    
    def test_login_route_with_valid_credentials(self, app, client, test_user, mock_auth_data):
        """Test login route with valid credentials."""
        with app.test_request_context():
            # Get CSRF token first
            csrf_token = get_csrf_token(client, '/login')
            
            response = client.post('/login', data={
                'username': test_user['username'],
                'password': test_user['password'],
                'csrf_token': csrf_token,
                'submit': 'Login as Administrator'
            }, follow_redirects=False)
            
            # Should redirect on successful login
            assert response.status_code == 302
    
    def test_login_route_with_invalid_credentials(self, app, client, test_user, mock_auth_data):
        """Test login route with invalid credentials."""
        with app.test_request_context():
            # Get CSRF token first
            csrf_token = get_csrf_token(client, '/login')
            
            response = client.post('/login', data={
                'username': test_user['username'],
                'password': 'wrongpassword',
                'csrf_token': csrf_token,
                'submit': 'Login as Administrator'
            })
            
            # Should return login page with error
            assert response.status_code == 200
            assert b'Invalid username or password' in response.data
    
    def test_api_key_route_authenticated(self, app, client, test_user, mock_auth_data):
        """Test API key route when authenticated."""
        with app.test_request_context():
            # Get CSRF token and login first
            csrf_token = get_csrf_token(client, '/login')
            client.post('/login', data={
                'username': test_user['username'],
                'password': test_user['password'],
                'csrf_token': csrf_token,
                'submit': 'Login as Administrator'
            })
            
            # Access API key route
            response = client.get('/auth/key')
            assert response.status_code == 200
            assert response.data.decode('utf-8') == test_user['user'].apikey
    
    def test_api_key_route_with_credentials(self, app, client, test_user, mock_auth_data):
        """Test API key route with username/password."""
        with app.test_request_context():
            # Get CSRF token from the API key page
            csrf_token = get_csrf_token(client, '/auth/key')
            
            response = client.post('/auth/key', data={
                'username': test_user['username'],
                'password': test_user['password'],
                'csrf_token': csrf_token,
                'submit': 'Login as Administrator'
            })
            
            assert response.status_code == 200
            assert response.data.decode('utf-8') == test_user['user'].apikey
    
    def test_register_route_requires_fresh_login(self, app, client, mock_auth_data):
        """Test that register route requires fresh login."""
        with app.test_request_context():
            response = client.get('/register')
            # Should be redirected to login or return 401
            assert response.status_code in [302, 401]
    
    def test_bearer_token_authentication(self, app, client, test_user, mock_auth_data):
        """Test Bearer token authentication for API access."""
        with app.test_request_context():
            # Access protected route with Bearer token
            headers = {'Authorization': f'Bearer {test_user["user"].apikey}'}
            response = client.get('/api/v1/', headers=headers)
            
            # Should be successful (or at least not unauthorized)
            assert response.status_code != 401
    
    def test_invalid_bearer_token(self, app, client, mock_auth_data):
        """Test invalid Bearer token is rejected."""
        with app.test_request_context():
            headers = {'Authorization': 'Bearer invalidtoken'}
            response = client.get('/api/v1/', headers=headers)
            
            # Should be unauthorized
            assert response.status_code == 401


class TestMongoDBBackendConsistency:
    """Test MongoDB backend consistency and reliability."""
    
    def test_data_persistence_across_operations(self, mock_auth_data):
        """Test that data persists correctly across multiple operations."""
        bcrypt = Bcrypt()
        username = "persistuser"
        password_hash = bcrypt.generate_password_hash("password").decode('utf-8')
        
        # Create user
        user = User.create_user(username, password_hash)
        original_id = user.id
        original_apikey = user.apikey
        
        # Perform multiple operations
        user.regenerate_api_key()
        new_password_hash = bcrypt.generate_password_hash("newpassword").decode('utf-8')
        user.update_password(new_password_hash)
        
        # Verify data consistency by re-fetching from database
        refreshed_user = User.find_by_id(original_id)
        assert refreshed_user is not None
        assert refreshed_user.id == original_id
        assert refreshed_user.username == username
        assert refreshed_user.password == new_password_hash
        assert refreshed_user.apikey != original_apikey
        assert len(refreshed_user.apikey) == 128
    
    def test_concurrent_operations_safety(self, mock_auth_data):
        """Test that concurrent-like operations don't cause data corruption."""
        bcrypt = Bcrypt()
        
        # Create multiple users rapidly
        users = []
        for i in range(10):
            username = f"concurrentuser{i}"
            password_hash = bcrypt.generate_password_hash(f"password{i}").decode('utf-8')
            user = User.create_user(username, password_hash)
            users.append(user)
        
        # Verify all users were created correctly
        all_users = User.get_all_users()
        assert len(all_users) == 10
        
        # Verify each user can be found individually
        for user in users:
            found_user = User.find_by_username(user.username)
            assert found_user is not None
            assert found_user.id == user.id
    
    def test_error_handling_consistency(self, mock_auth_data):
        """Test consistent error handling across operations."""
        # Test operations on non-existent user
        non_existent_user_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
        
        user = User.find_by_id(non_existent_user_id)
        assert user is None
        
        user = User.find_by_username("nonexistent")
        assert user is None
        
        user = User.find_by_api_key("a" * 128)
        assert user is None
        
        assert User.username_exists("nonexistent") is False