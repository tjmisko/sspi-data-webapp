"""Behavior of `sspi push` when the local series is empty.

Re-imputing a series that no longer needs imputed rows (ARMEXP after the
SIPRI zero-TIV cleaner, RULELW and EDEMOC on V-Dem v16) leaves zero local
imputed rows. The old command printed "No local observations" and returned
without touching Remote, so stale remote imputed rows survived and later
duplicated the new observed rows at finalize time.
"""
from click.testing import CliRunner
import pytest

import cli.commands.push as push_module
from cli.commands.push import push


class FakeResponse:
    def __init__(self, payload=None, text="ok", raise_on_json=False):
        self.payload = payload
        self.text = text
        self.raise_on_json = raise_on_json

    def json(self):
        if self.raise_on_json:
            raise ValueError("not JSON")
        return self.payload


class FakeConnector:
    """Records every call; serves canned local and remote query payloads."""

    def __init__(self, local_payload, remote_query_response):
        self.local_payload = local_payload
        self.remote_query_response = remote_query_response
        self.calls = []
        self.loads = []

    def call(self, request_string, method="GET", remote=False, **kwargs):
        self.calls.append((method, remote, request_string))
        if method == "DELETE":
            return FakeResponse(text=f"Deleted observations via {request_string}")
        if remote:
            return self.remote_query_response
        return FakeResponse(payload=self.local_payload)

    def load(self, obs_lst, database_name, remote=False):
        self.loads.append((database_name, remote, obs_lst))
        return FakeResponse(text="Inserted")

    def remote_deletes(self):
        return [c for c in self.calls if c[0] == "DELETE" and c[1]]


def install_fake_connector(monkeypatch, local_payload, remote_query_response):
    fake_connector = FakeConnector(local_payload, remote_query_response)
    monkeypatch.setattr(push_module, "SSPIDatabaseConnector", lambda: fake_connector)
    return fake_connector


STALE_REMOTE_ROWS = [
    {"IndicatorCode": "ARMEXP", "CountryCode": "ARE", "Year": 2005, "Value": 579.15},
    {"IndicatorCode": "ARMEXP", "CountryCode": "BGD", "Year": 2005, "Value": 579.15},
]


def test_should_delete_remote_series_when_local_is_empty_and_user_confirms(monkeypatch):
    fake_connector = install_fake_connector(
        monkeypatch, [], FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(push, ["imputed", "armexp", "-y"], input="y\n")
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == [
        ("DELETE", True, "/api/v1/delete/series/sspi_imputed_data/ARMEXP")
    ]
    assert fake_connector.loads == []
    assert "2 observations" in result.output


def test_should_delete_remote_series_without_prompt_when_delete_remote_if_empty_is_set(monkeypatch):
    fake_connector = install_fake_connector(
        monkeypatch, [], FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(
        push, ["imputed", "RULELW", "-y", "--delete-remote-if-empty"], input=""
    )
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == [
        ("DELETE", True, "/api/v1/delete/series/sspi_imputed_data/RULELW")
    ]
    assert fake_connector.loads == []


def test_should_warn_and_name_delete_command_when_local_is_empty_and_user_declines(monkeypatch):
    fake_connector = install_fake_connector(
        monkeypatch, [], FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(push, ["imputed", "EDEMOC", "-y"], input="n\n")
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == []
    assert "stale" in result.output
    assert "LEFT IN PLACE" in result.output
    assert "sspi delete series sspi_imputed_data EDEMOC -r" in result.output


def test_should_not_delete_remote_by_default_when_yes_to_all_and_no_input(monkeypatch):
    """-y confirms the push itself, not a remote wipe of a series with no local rows."""
    fake_connector = install_fake_connector(
        monkeypatch, [], FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(push, ["imputed", "ARMEXP", "-y"], input="\n")
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == []
    assert "LEFT IN PLACE" in result.output


def test_should_do_nothing_when_local_and_remote_are_both_empty(monkeypatch):
    fake_connector = install_fake_connector(monkeypatch, [], FakeResponse(payload=[]))
    result = CliRunner().invoke(push, ["imputed", "ARMEXP", "-y"], input="")
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == []
    assert fake_connector.loads == []
    assert "nothing to push" in result.output


@pytest.mark.parametrize("remote_query_response", [
    FakeResponse(raise_on_json=True),
    FakeResponse(payload={"error": "Invalid Database Provided"}),
])
def test_should_warn_with_unknown_count_when_remote_query_fails(monkeypatch, remote_query_response):
    fake_connector = install_fake_connector(monkeypatch, [], remote_query_response)
    result = CliRunner().invoke(push, ["imputed", "ARMEXP", "-y"], input="n\n")
    assert result.exit_code == 0, result.output
    assert "an unknown number of" in result.output
    assert fake_connector.remote_deletes() == []
    assert "sspi delete series sspi_imputed_data ARMEXP -r" in result.output


def test_should_replace_remote_series_when_local_has_rows(monkeypatch):
    local_rows = [{"IndicatorCode": "ARMEXP", "CountryCode": "ARE", "Year": 2005, "Value": 0}]
    fake_connector = install_fake_connector(
        monkeypatch, local_rows, FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(push, ["indicator", "ARMEXP", "-y"], input="")
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == [
        ("DELETE", True, "/api/v1/delete/series/indicator/ARMEXP")
    ]
    assert fake_connector.loads == [("indicator", True, local_rows)]


def test_should_not_touch_remote_when_local_query_returns_an_error_object(monkeypatch):
    fake_connector = install_fake_connector(
        monkeypatch, {"error": "Invalid Database Provided"}, FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(push, ["bogus", "ARMEXP", "-y"], input="y\n")
    assert result.exit_code == 0, result.output
    assert fake_connector.remote_deletes() == []
    assert fake_connector.loads == []


def test_should_not_touch_remote_when_push_is_not_confirmed(monkeypatch):
    fake_connector = install_fake_connector(
        monkeypatch, [], FakeResponse(payload=STALE_REMOTE_ROWS)
    )
    result = CliRunner().invoke(push, ["imputed", "ARMEXP"], input="n\n")
    assert result.exit_code == 0, result.output
    assert fake_connector.calls == []
