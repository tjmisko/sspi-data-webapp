from database_connector import SSPIDatabaseConnector


def test_connector_login():
    connector = SSPIDatabaseConnector()
    assert connector.local_token is not None
    assert connector.remote_token is not None
