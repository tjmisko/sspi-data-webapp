from database_connector import SSPIDatabaseConnector


def test_connector_login():
    connector = SSPIDatabaseConnector()
    assert connector.token is not None
