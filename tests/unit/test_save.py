import pytest
from unittest.mock import patch, mock_open
from flask import url_for
from sspi_flask_app.models.usermodel import User, db
import secrets


@pytest.fixture
def login(client, app):
    """Create and log in a real test user, then clean up after."""
    with app.app_context():
        user = User(
            username='testuser',
            password='testpassword',  # Dummy password
            secretkey=secrets.token_hex(16),
            apikey=secrets.token_hex(32)
        )
        db.session.add(user)
        db.session.commit()

        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)

    yield user

    # Cleanup phase: explicitly delete the user
    with app.app_context():
        db.session.delete(user)
        db.session.commit()


def test_save_database(client, login):
    """Test saving a specific database to local storage."""
    with patch('sspi_flask_app.api.core.save.lookup_database') as mock_lookup_db, \
         patch('sspi_flask_app.api.resources.utilities.parse_json') as mock_parse_json, \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as mock_file:

        mock_lookup_db.return_value.find.return_value = []
        mock_parse_json.return_value = []

        response = client.get(url_for('api_bp.save_bp.save_database', database_name='test_db'))

        assert response.status_code == 200
        mock_lookup_db.assert_called_once_with('test_db')
        mock_file.assert_called_once()  # Check that a file was attempted to be written


def test_save_all(client, login):
    """Test saving all databases to local storage."""
    with patch('sspi_flask_app.api.core.save.sspidb') as mock_sspidb, \
         patch('sspi_flask_app.api.core.save.lookup_database') as mock_lookup_db, \
         patch('sspi_flask_app.api.resources.utilities.parse_json') as mock_parse_json, \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as mock_file:

        mock_sspidb.list_collection_names.return_value = ['db1', 'db2']
        mock_lookup_db.return_value.find.return_value = []
        mock_parse_json.return_value = []

        response = client.get(url_for('api_bp.save_bp.save_all'))

        assert response.status_code == 200
        assert b"Dumped 0 records from db1 to" in response.data
        assert b"Dumped 0 records from db1 to" in response.data
        assert mock_file.call_count == 2  # Two databases, two file writes
