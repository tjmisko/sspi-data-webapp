import pytest
import secrets
from unittest.mock import patch, MagicMock
from bson import ObjectId
from sspi_flask_app.models.usermodel import User
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture(scope="function")
def test_user_db():
    """Create a clean test database for user data."""
    test_db = sspidb.test_users_model
    test_db.delete_many({})
    yield test_db
    test_db.delete_many({})
    sspidb.drop_collection(test_db)


@pytest.fixture(scope="function")
def mock_sspi_user_data(test_user_db):
    """Mock sspi_user_data to use test database."""
    with patch('sspi_flask_app.models.usermodel.sspi_user_data') as mock:
        from sspi_flask_app.models.database.sspi_user_data import SSPIUserData
        mock_wrapper = SSPIUserData(test_user_db)
        
        # Set up mock methods to use actual wrapper
        mock.find_by_username = mock_wrapper.find_by_username
        mock.find_by_api_key = mock_wrapper.find_by_api_key
        mock.find_by_id = mock_wrapper.find_by_id
        mock.create_user = mock_wrapper.create_user
        mock.username_exists = mock_wrapper.username_exists
        mock.update_password = mock_wrapper.update_password
        mock.regenerate_api_key = mock_wrapper.regenerate_api_key
        mock.get_all_users = mock_wrapper.get_all_users
        mock.delete_user = mock_wrapper.delete_user
        
        yield mock


@pytest.fixture(scope="session")
def sample_user_doc():
    """Sample user document for testing."""
    return {
        "_id": ObjectId(),
        "username": "testuser",
        "password": "$2b$12$KIXTqXFgLCJHE5lZ2IxY2OHN6rN8wZr4gQdN1TlRfV9rK.2NzY3Jm",
        "apikey": "a" * 128,
        "secretkey": "b" * 64,
        "roles": ["user"]
    }


@pytest.fixture(scope="session")
def sample_user_docs():
    """Multiple sample user documents for testing."""
    return [
        {
            "_id": ObjectId(),
            "username": "user1",
            "password": "$2b$12$yHFh700tJ.4BxUs1/0b2cec0dfaBtNxt1lEsciJrGJUx9W4k7yc4q",  # Valid bcrypt hash
            "apikey": "a" * 128,
            "secretkey": "b" * 64,
            "roles": ["user"]
        },
        {
            "_id": ObjectId(),
            "username": "user2",
            "password": "$2b$12$6ptOjmr52NjjHF0vhh5puua4gE6UO4GjwthW47rwToT1HFBOTj5YC",  # Valid bcrypt hash
            "apikey": "c" * 128,
            "secretkey": "d" * 64,
            "roles": ["user"]
        },
        {
            "_id": ObjectId(),
            "username": "user3",
            "password": "$2b$12$ZWxaFzpcl9bUCl9pEUGsUemeoU8VmwxdyiulrtIj3GidZ1hAQzpsK",  # Valid bcrypt hash
            "apikey": "e" * 128,
            "secretkey": "f" * 64,
            "roles": ["user"]
        }
    ]


class TestUserModelInitialization:
    """Test User model initialization."""
    
    def test_user_init_valid(self, sample_user_doc):
        """Test creating User from valid document."""
        user = User(sample_user_doc)
        
        assert user.id == str(sample_user_doc["_id"])
        assert user.username == sample_user_doc["username"]
        assert user.password == sample_user_doc["password"]
        assert user.apikey == sample_user_doc["apikey"]
        assert user.secretkey == sample_user_doc["secretkey"]
    
    def test_user_init_none_document(self):
        """Test that initializing with None raises ValueError."""
        with pytest.raises(ValueError, match="User document cannot be None"):
            User(None)
    
    def test_get_id(self, sample_user_doc):
        """Test get_id method returns string ID."""
        user = User(sample_user_doc)
        assert user.get_id() == str(sample_user_doc["_id"])
        assert isinstance(user.get_id(), str)
    
    def test_repr(self, sample_user_doc):
        """Test string representation of User."""
        user = User(sample_user_doc)
        assert repr(user) == f'<User {sample_user_doc["username"]}>'


class TestUserModelStaticMethods:
    """Test User model static methods."""
    
    def test_find_by_username_exists(self, mock_sspi_user_data, sample_user_doc):
        """Test finding existing user by username."""
        # Insert test user into mock database
        mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        
        user = User.find_by_username(sample_user_doc["username"])
        assert user is not None
        assert isinstance(user, User)
        assert user.username == sample_user_doc["username"]
    
    def test_find_by_username_not_exists(self, mock_sspi_user_data):
        """Test finding non-existent user by username."""
        user = User.find_by_username("nonexistent")
        assert user is None
    
    def test_find_by_api_key_exists(self, mock_sspi_user_data, sample_user_doc):
        """Test finding existing user by API key."""
        # Insert test user
        mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        
        user = User.find_by_api_key(sample_user_doc["apikey"])
        assert user is not None
        assert isinstance(user, User)
        assert user.apikey == sample_user_doc["apikey"]
    
    def test_find_by_api_key_not_exists(self, mock_sspi_user_data):
        """Test finding non-existent user by API key."""
        user = User.find_by_api_key("nonexistent" + "a" * 118)
        assert user is None
    
    def test_find_by_id_exists(self, mock_sspi_user_data, sample_user_doc):
        """Test finding existing user by ID."""
        # Insert test user
        user_id = mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        
        user = User.find_by_id(user_id)
        assert user is not None
        assert isinstance(user, User)
        assert user.id == user_id
    
    def test_find_by_id_not_exists(self, mock_sspi_user_data):
        """Test finding non-existent user by ID."""
        user = User.find_by_id("invalid_id")
        assert user is None
    
    def test_create_user_success(self, mock_sspi_user_data):
        """Test successful user creation."""
        username = "newuser"
        password_hash = "$2b$12$KIXTqXFgLCJHE5lZ2IxY2OHN6rN8wZr4gQdN1TlRfV9rK.2NzY3Jm"  # Valid bcrypt hash
        api_key = "a" * 128
        secret_key = "b" * 64

        user = User.create_user(username, password_hash, email=None, api_key=api_key, secret_key=secret_key)
        assert user is not None
        assert isinstance(user, User)
        assert user.username == username
        assert user.password == password_hash
        assert user.apikey == api_key
        assert user.secretkey == secret_key
    
    def test_create_user_auto_keys(self, mock_sspi_user_data):
        """Test user creation with auto-generated keys."""
        username = "autokeyuser"
        password_hash = "$2b$12$6ptOjmr52NjjHF0vhh5puua4gE6UO4GjwthW47rwToT1HFBOTj5YC"  # Valid bcrypt hash
        
        user = User.create_user(username, password_hash)
        assert user is not None
        assert len(user.apikey) == 128
        assert len(user.secretkey) == 64
    
    def test_create_user_validation_error(self, mock_sspi_user_data):
        """Test user creation with validation error."""
        with pytest.raises(InvalidDocumentFormatError):
            User.create_user("ab", "invalid_password")  # Too short username, invalid password
    
    def test_username_exists_true(self, mock_sspi_user_data, sample_user_doc):
        """Test username_exists returns True for existing username."""
        mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        
        assert User.username_exists(sample_user_doc["username"]) is True
    
    def test_username_exists_false(self, mock_sspi_user_data):
        """Test username_exists returns False for non-existent username."""
        assert User.username_exists("nonexistent") is False
    
    def test_get_all_users(self, mock_sspi_user_data, sample_user_docs):
        """Test getting all users."""
        # Create multiple users
        for doc in sample_user_docs:
            mock_sspi_user_data.create_user(
                doc["username"], doc["password"],
                email=None, api_key=doc["apikey"], secret_key=doc["secretkey"]
            )
        
        users = User.get_all_users()
        assert len(users) == len(sample_user_docs)
        assert all(isinstance(user, User) for user in users)
        
        usernames = [user.username for user in users]
        for doc in sample_user_docs:
            assert doc["username"] in usernames


class TestUserModelInstanceMethods:
    """Test User model instance methods."""
    
    def test_update_password_success(self, mock_sspi_user_data, sample_user_doc):
        """Test successful password update."""
        # Create user
        user_id = mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        user = User.find_by_id(user_id)
        
        new_password = "$2b$12$ZWxaFzpcl9bUCl9pEUGsUemeoU8VmwxdyiulrtIj3GidZ1hAQzpsK"  # Valid bcrypt hash
        success = user.update_password(new_password)
        
        assert success is True
        assert user.password == new_password
    
    def test_update_password_failure(self, mock_sspi_user_data, sample_user_doc):
        """Test password update failure."""
        user = User(sample_user_doc)
        
        # Mock the wrapper method to return False
        with patch.object(mock_sspi_user_data, 'update_password', return_value=False):
            success = user.update_password("$2b$12$KIXTqXFgLCJHE5lZ2IxY2OHN6rN8wZr4gQdN1TlRfV9rK.2NzY3Jm")
            assert success is False
            # Original password should be unchanged
            assert user.password == sample_user_doc["password"]
    
    def test_regenerate_api_key_success(self, mock_sspi_user_data, sample_user_doc):
        """Test successful API key regeneration."""
        # Create user
        user_id = mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        user = User.find_by_id(user_id)
        original_api_key = user.apikey
        
        new_api_key = user.regenerate_api_key()
        
        assert new_api_key is not None
        assert len(new_api_key) == 128
        assert new_api_key != original_api_key
        assert user.apikey == new_api_key
    
    def test_regenerate_api_key_failure(self, mock_sspi_user_data, sample_user_doc):
        """Test API key regeneration failure."""
        user = User(sample_user_doc)
        original_api_key = user.apikey
        
        # Mock the wrapper method to return None
        with patch.object(mock_sspi_user_data, 'regenerate_api_key', return_value=None):
            new_api_key = user.regenerate_api_key()
            assert new_api_key is None
            # Original API key should be unchanged
            assert user.apikey == original_api_key
    
    def test_delete_success(self, mock_sspi_user_data, sample_user_doc):
        """Test successful user deletion."""
        # Create user
        user_id = mock_sspi_user_data.create_user(
            sample_user_doc["username"],
            sample_user_doc["password"],
            email=None,
            api_key=sample_user_doc["apikey"],
            secret_key=sample_user_doc["secretkey"]
        )
        user = User.find_by_id(user_id)
        
        success = user.delete()
        assert success is True
        
        # Verify user is deleted
        deleted_user = User.find_by_id(user_id)
        assert deleted_user is None
    
    def test_delete_failure(self, mock_sspi_user_data, sample_user_doc):
        """Test user deletion failure."""
        user = User(sample_user_doc)
        
        # Mock the wrapper method to return False
        with patch.object(mock_sspi_user_data, 'delete_user', return_value=False):
            success = user.delete()
            assert success is False


class TestUserModelFlaskLoginIntegration:
    """Test Flask-Login integration."""
    
    def test_is_authenticated_default(self, sample_user_doc):
        """Test that User has default Flask-Login authentication properties."""
        user = User(sample_user_doc)
        
        # UserMixin provides default implementations
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False
    
    def test_get_id_string_format(self, sample_user_doc):
        """Test that get_id returns string for Flask-Login."""
        user = User(sample_user_doc)
        user_id = user.get_id()
        
        assert isinstance(user_id, str)
        assert user_id == str(sample_user_doc["_id"])