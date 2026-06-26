from connector import SSPIDatabaseConnector


def test_connector_login():
    connector = SSPIDatabaseConnector()
    assert connector.local_token is not None
    assert connector.remote_token is not None


def test_load_posts_single_encoded_list(monkeypatch):
    """load() should send the observation list directly as the JSON body
    (single-encode), not a json.dumps() string (the old double-encode that
    the server then had to json.loads a second time)."""
    connector = SSPIDatabaseConnector()
    captured = {}

    class _FakeResponse:
        status_code = 200
        text = "ok"

    def _fake_post(endpoint, json=None, **kwargs):
        captured["endpoint"] = endpoint
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr(connector.local_session, "post", _fake_post)
    observations = [
        {"CountryCode": "USA", "Value": 1},
        {"CountryCode": "CAN", "Value": 2},
    ]
    connector.load(observations, "sspi_clean_api_data", remote=False)

    assert captured["json"] == observations
    assert not isinstance(captured["json"], str)
    assert captured["endpoint"].endswith("/api/v1/load/sspi_clean_api_data")
