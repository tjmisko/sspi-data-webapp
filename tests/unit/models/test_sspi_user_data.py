import pytest
import secrets
from bson import ObjectId
from sspi_flask_app.models.database.sspi_user_data import SSPIUserData
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture(scope="function")
def test_user_db():
    """Create a clean test database for user data."""
    test_db = sspidb.test_users
    test_db.delete_many({})
    yield test_db
    test_db.delete_many({})
    sspidb.drop_collection(test_db)


@pytest.fixture(scope="function")
def user_wrapper(test_user_db):
    """Create SSPIUserData wrapper for testing."""
    wrapper = SSPIUserData(test_user_db)
    yield wrapper


@pytest.fixture(scope="session")
def valid_user_docs():
    """Valid user documents for testing."""
    return {
        "user1": {
            "username": "testuser1",
            "password": "$2b$12$yHFh700tJ.4BxUs1/0b2cec0dfaBtNxt1lEsciJrGJUx9W4k7yc4q",  # Valid bcrypt hash
            "apikey": "a" * 128,  # 128 char hex string
            "secretkey": "b" * 64  # 64 char hex string
        },
        "user2": {
            "username": "admin",
            "password": "$2b$12$6ptOjmr52NjjHF0vhh5puua4gE6UO4GjwthW47rwToT1HFBOTj5YC",  # Valid bcrypt hash
            "apikey": "c" * 128,
            "secretkey": "d" * 64
        },
        "user3": {
            "username": "testuser3",
            "password": "$2b$12$ZWxaFzpcl9bUCl9pEUGsUemeoU8VmwxdyiulrtIj3GidZ1hAQzpsK",  # Valid bcrypt hash
            "apikey": "e" * 128,
            "secretkey": "f" * 64
        }
    }


@pytest.fixture(scope="session")
def invalid_user_docs():
    """Invalid user documents for testing validation."""
    return {
        "missing_username": {
            "password": "$2b$12$validhash",
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "invalid_username_short": {
            "username": "ab",  # Too short
            "password": "$2b$12$validhash",
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "invalid_username_long": {
            "username": "a" * 25,  # Too long
            "password": "$2b$12$validhash",
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "invalid_username_chars": {
            "username": "test@user",  # Invalid characters
            "password": "$2b$12$validhash",
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "missing_password": {
            "username": "testuser",
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "invalid_password_format": {
            "username": "testuser",
            "password": "plaintext",  # Not bcrypt hash
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "invalid_password_short": {
            "username": "testuser",
            "password": "$2b$12$short",  # Too short for bcrypt
            "apikey": "a" * 128,
            "secretkey": "b" * 64
        },
        "invalid_apikey_length": {
            "username": "testuser",
            "password": "$2b$12$yHFh700tJ.4BxUs1/0b2cec0dfaBtNxt1lEsciJrGJUx9W4k7yc4q",  # Valid bcrypt hash
            "apikey": "a" * 50,  # Wrong length
            "secretkey": "b" * 64
        },
        "invalid_apikey_chars": {
            "username": "testuser",
            "password": "$2b$12$yHFh700tJ.4BxUs1/0b2cec0dfaBtNxt1lEsciJrGJUx9W4k7yc4q",  # Valid bcrypt hash
            "apikey": "G" * 128,  # Invalid hex chars
            "secretkey": "b" * 64
        },
        "invalid_secretkey_length": {
            "username": "testuser",
            "password": "$2b$12$yHFh700tJ.4BxUs1/0b2cec0dfaBtNxt1lEsciJrGJUx9W4k7yc4q",  # Valid bcrypt hash
            "apikey": "a" * 128,
            "secretkey": "b" * 30  # Wrong length
        }
    }


class TestSSPIUserDataValidation:
    """Test document validation methods."""
    
    def test_validate_valid_documents(self, user_wrapper, valid_user_docs):
        """Test that valid documents pass validation."""
        for doc in valid_user_docs.values():
            # Should not raise any exception
            user_wrapper.validate_document_format(doc)
    
    def test_validate_username_missing(self, user_wrapper, invalid_user_docs):
        """Test validation fails for missing username."""
        with pytest.raises(InvalidDocumentFormatError, match="'username' is a required field"):
            user_wrapper.validate_username(invalid_user_docs["missing_username"])
    
    def test_validate_username_too_short(self, user_wrapper, invalid_user_docs):
        """Test validation fails for username too short."""
        with pytest.raises(InvalidDocumentFormatError, match="must be 4-20 characters long"):
            user_wrapper.validate_username(invalid_user_docs["invalid_username_short"])
    
    def test_validate_username_too_long(self, user_wrapper, invalid_user_docs):
        """Test validation fails for username too long."""
        with pytest.raises(InvalidDocumentFormatError, match="must be 4-20 characters long"):
            user_wrapper.validate_username(invalid_user_docs["invalid_username_long"])
    
    def test_validate_username_invalid_chars(self, user_wrapper, invalid_user_docs):
        """Test validation fails for invalid username characters."""
        with pytest.raises(InvalidDocumentFormatError, match="can only contain letters, numbers, and underscores"):
            user_wrapper.validate_username(invalid_user_docs["invalid_username_chars"])
    
    def test_validate_password_missing(self, user_wrapper, invalid_user_docs):
        """Test validation fails for missing password."""
        with pytest.raises(InvalidDocumentFormatError, match="'password' is a required field"):
            user_wrapper.validate_password_hash(invalid_user_docs["missing_password"])
    
    def test_validate_password_invalid_format(self, user_wrapper, invalid_user_docs):
        """Test validation fails for invalid password format."""
        with pytest.raises(InvalidDocumentFormatError, match="must be a valid bcrypt hash"):
            user_wrapper.validate_password_hash(invalid_user_docs["invalid_password_format"])
    
    def test_validate_apikey_invalid_length(self, user_wrapper, invalid_user_docs):
        """Test validation fails for invalid API key length."""
        with pytest.raises(InvalidDocumentFormatError, match="must be 128 characters long"):
            user_wrapper.validate_api_key(invalid_user_docs["invalid_apikey_length"])
    
    def test_validate_apikey_invalid_chars(self, user_wrapper, invalid_user_docs):
        """Test validation fails for invalid API key characters."""
        with pytest.raises(InvalidDocumentFormatError, match="must be a valid hexadecimal string"):
            user_wrapper.validate_api_key(invalid_user_docs["invalid_apikey_chars"])
    
    def test_validate_secretkey_invalid_length(self, user_wrapper, invalid_user_docs):
        """Test validation fails for invalid secret key length."""
        with pytest.raises(InvalidDocumentFormatError, match="must be 64 characters long"):
            user_wrapper.validate_secret_key(invalid_user_docs["invalid_secretkey_length"])


class TestSSPIUserDataCRUD:
    """Test CRUD operations."""
    
    def test_create_user_valid(self, user_wrapper):
        """Test creating a valid user."""
        username = "newuser"
        password_hash = "$2b$12$KIXTqXFgLCJHE5lZ2IxY2OHN6rN8wZr4gQdN1TlRfV9rK.2NzY3Jm"
        api_key = "a" * 128
        secret_key = "b" * 64
        
        user_id = user_wrapper.create_user(username, password_hash, api_key, secret_key)
        
        assert user_id is not None
        assert ObjectId.is_valid(user_id)
        
        # Verify user was created
        user_doc = user_wrapper.find_by_id(user_id)
        assert user_doc is not None
        assert user_doc["username"] == username
        assert user_doc["password"] == password_hash
        assert user_doc["apikey"] == api_key
        assert user_doc["secretkey"] == secret_key
    
    def test_create_user_auto_generate_keys(self, user_wrapper):
        """Test creating user with auto-generated keys."""
        username = "autokeyuser"
        password_hash = "$2b$12$KIXTqXFgLCJHE5lZ2IxY2OHN6rN8wZr4gQdN1TlRfV9rK.2NzY3Jm"
        
        user_id = user_wrapper.create_user(username, password_hash)
        
        user_doc = user_wrapper.find_by_id(user_id)
        assert len(user_doc["apikey"]) == 128
        assert len(user_doc["secretkey"]) == 64
        # Verify they're valid hex strings
        int(user_doc["apikey"], 16)  # Should not raise exception
        int(user_doc["secretkey"], 16)  # Should not raise exception
    
    def test_create_user_duplicate_username(self, user_wrapper, valid_user_docs):
        """Test that creating user with duplicate username fails."""
        # Create first user
        user1 = valid_user_docs["user1"]
        user_wrapper.create_user(
            user1["username"], user1["password"], 
            user1["apikey"], user1["secretkey"]
        )
        
        # Try to create second user with same username
        with pytest.raises(InvalidDocumentFormatError, match="already exists"):
            user_wrapper.create_user(
                user1["username"], user1["password"],
                "d" + "a" * 127, "d" + "b" * 63  # Correct lengths: 128 and 64
            )
    
    def test_find_by_username(self, user_wrapper, valid_user_docs):
        """Test finding user by username."""
        user_doc = valid_user_docs["user1"]
        user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        found_user = user_wrapper.find_by_username(user_doc["username"])
        assert found_user is not None
        assert found_user["username"] == user_doc["username"]
        
        # Test non-existent user
        not_found = user_wrapper.find_by_username("nonexistent")
        assert not_found is None
    
    def test_find_by_api_key(self, user_wrapper, valid_user_docs):
        """Test finding user by API key."""
        user_doc = valid_user_docs["user1"]
        user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        found_user = user_wrapper.find_by_api_key(user_doc["apikey"])
        assert found_user is not None
        assert found_user["apikey"] == user_doc["apikey"]
        
        # Test non-existent API key
        not_found = user_wrapper.find_by_api_key("nonexistent" + "a" * 118)
        assert not_found is None
    
    def test_find_by_id(self, user_wrapper, valid_user_docs):
        """Test finding user by ID."""
        user_doc = valid_user_docs["user1"]
        user_id = user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        found_user = user_wrapper.find_by_id(user_id)
        assert found_user is not None
        # Handle ObjectId format from json_util.dumps
        if isinstance(found_user["_id"], dict) and "$oid" in found_user["_id"]:
            assert found_user["_id"]["$oid"] == user_id
        else:
            assert str(found_user["_id"]) == user_id
        
        # Test invalid ID
        not_found = user_wrapper.find_by_id("invalid_id")
        assert not_found is None
    
    def test_update_password(self, user_wrapper, valid_user_docs):
        """Test updating user password."""
        user_doc = valid_user_docs["user1"]
        user_id = user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        new_password = "$2b$12$ZWxaFzpcl9bUCl9pEUGsUemeoU8VmwxdyiulrtIj3GidZ1hAQzpsK"  # Valid bcrypt hash
        success = user_wrapper.update_password(user_id, new_password)
        assert success is True
        
        # Verify password was updated
        updated_user = user_wrapper.find_by_id(user_id)
        assert updated_user["password"] == new_password
    
    def test_regenerate_api_key(self, user_wrapper, valid_user_docs):
        """Test regenerating API key."""
        user_doc = valid_user_docs["user1"]
        user_id = user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        new_api_key = user_wrapper.regenerate_api_key(user_id)
        assert new_api_key is not None
        assert len(new_api_key) == 128
        assert new_api_key != user_doc["apikey"]
        
        # Verify API key was updated
        updated_user = user_wrapper.find_by_id(user_id)
        assert updated_user["apikey"] == new_api_key
    
    def test_username_exists(self, user_wrapper, valid_user_docs):
        """Test checking if username exists."""
        user_doc = valid_user_docs["user1"]
        
        # Initially should not exist
        assert user_wrapper.username_exists(user_doc["username"]) is False
        
        # Create user
        user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        # Should now exist
        assert user_wrapper.username_exists(user_doc["username"]) is True
        assert user_wrapper.username_exists("nonexistent") is False
    
    def test_get_all_users(self, user_wrapper, valid_user_docs):
        """Test getting all users."""
        # Initially empty
        users = user_wrapper.get_all_users()
        assert len(users) == 0
        
        # Create multiple users
        for user_doc in valid_user_docs.values():
            user_wrapper.create_user(
                user_doc["username"], user_doc["password"],
                user_doc["apikey"], user_doc["secretkey"]
            )
        
        # Should return all users
        users = user_wrapper.get_all_users()
        assert len(users) == len(valid_user_docs)
        usernames = [user["username"] for user in users]
        for user_doc in valid_user_docs.values():
            assert user_doc["username"] in usernames
    
    def test_delete_user(self, user_wrapper, valid_user_docs):
        """Test deleting a user."""
        user_doc = valid_user_docs["user1"]
        user_id = user_wrapper.create_user(
            user_doc["username"], user_doc["password"],
            user_doc["apikey"], user_doc["secretkey"]
        )
        
        # User should exist
        assert user_wrapper.find_by_id(user_id) is not None
        
        # Delete user
        success = user_wrapper.delete_user(user_id)
        assert success is True
        
        # User should no longer exist
        assert user_wrapper.find_by_id(user_id) is None
        
        # Deleting non-existent user should return False
        success = user_wrapper.delete_user(user_id)
        assert success is False


class TestSSPIUserDataIndexes:
    """Test database indexing functionality."""
    
    def test_create_indexes(self, user_wrapper):
        """Test creating database indexes."""
        # This should not raise any exceptions
        user_wrapper.create_indexes()
        
        # We can't easily test index creation without accessing MongoDB internals,
        # but we can verify the method runs without error
        assert True  # If we get here, indexes were created successfully