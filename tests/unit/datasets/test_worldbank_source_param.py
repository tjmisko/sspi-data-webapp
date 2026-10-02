"""
Unit tests for the optional ``source`` / organization override parameters on
``collect_wb_data``. These monkeypatch ``requests.get`` and the raw-data
insert so nothing touches the network or the database.
"""
import frontmatter
import os
import pytest

import sspi_flask_app.api.datasource.worldbank as worldbank


REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

FAKE_PAGE_ONE_ROWS = [
    {
        "indicator": {"id": "X", "value": "X name"},
        "country": {"id": "US", "value": "United States"},
        "countryiso3code": "USA",
        "date": "2024",
        "value": 1.0,
    }
]


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _install_fakes(monkeypatch, pages=1):
    """Capture every URL requested and every source_info stamped."""
    captured = {"urls": [], "source_infos": []}

    def _fake_get(url, *args, **kwargs):
        captured["urls"].append(url)
        return _FakeResponse([{"pages": pages}, FAKE_PAGE_ONE_ROWS])

    def _fake_raw_insert_many(document_list, source_info, **kwargs):
        captured["source_infos"].append(source_info)
        return len(document_list)

    monkeypatch.setattr(worldbank.requests, "get", _fake_get)
    monkeypatch.setattr(
        worldbank.sspi_raw_api_data, "raw_insert_many", _fake_raw_insert_many
    )
    monkeypatch.setattr(worldbank.time, "sleep", lambda _seconds: None)
    return captured


def _load_doc_source(org_folder, dataset_folder):
    doc_path = os.path.join(
        REPO_ROOT, "datasets", org_folder, dataset_folder, "documentation.md"
    )
    return frontmatter.load(doc_path).metadata["Source"]


def test_should_build_legacy_url_without_source_when_source_omitted(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(worldbank.collect_wb_data("GC.TAX.TOTL.GD.ZS", username="tester"))
    assert captured["urls"][0] == (
        "https://api.worldbank.org/v2/country/all/indicator/"
        "GC.TAX.TOTL.GD.ZS?per_page=1000&format=json"
    )
    assert captured["urls"][1] == (
        "https://api.worldbank.org/v2/country/all/indicator/"
        "GC.TAX.TOTL.GD.ZS?per_page=1000&format=json&page=1"
    )
    assert all("source=" not in url for url in captured["urls"])


def test_should_stamp_unchanged_wb_source_info_when_no_overrides_given(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(worldbank.collect_wb_data("GC.TAX.TOTL.GD.ZS", username="tester"))
    stamped = captured["source_infos"][0]
    assert stamped["OrganizationName"] == "World Bank"
    assert stamped["OrganizationCode"] == "WB"
    assert stamped["OrganizationSeriesCode"] == "GC.TAX.TOTL.GD.ZS"
    assert stamped["QueryCode"] == "GC.TAX.TOTL.GD.ZS"
    assert stamped["BaseURL"] == (
        "https://api.worldbank.org/v2/country/all/indicator/GC.TAX.TOTL.GD.ZS"
    )
    assert stamped["URL"] == captured["urls"][1]
    assert set(stamped.keys()) == {
        "OrganizationName", "OrganizationCode", "OrganizationSeriesCode",
        "QueryCode", "URL", "BaseURL",
    }


def test_should_append_source_query_param_when_source_given(monkeypatch):
    captured = _install_fakes(monkeypatch, pages=2)
    list(worldbank.collect_wb_data("GOV_WGI_GE.EST", source=3, username="tester"))
    assert captured["urls"][0].endswith("?per_page=1000&format=json&source=3")
    assert captured["urls"][1].endswith("&source=3&page=1")
    assert captured["urls"][2].endswith("&source=3&page=2")
    assert all("&source=3" in url for url in captured["urls"])


def test_should_keep_base_url_free_of_source_param_when_source_given(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(worldbank.collect_wb_data("GOV_WGI_GE.EST", source=3, username="tester"))
    stamped = captured["source_infos"][0]
    assert stamped["BaseURL"] == (
        "https://api.worldbank.org/v2/country/all/indicator/GOV_WGI_GE.EST"
    )
    assert "source=3" in stamped["URL"]


def test_should_stamp_originator_org_when_organization_override_given(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(worldbank.collect_wb_data(
        "SG.GEN.PARL.ZS",
        organization_code="IPU",
        organization_name="Inter-Parliamentary Union",
        username="tester",
    ))
    stamped = captured["source_infos"][0]
    assert stamped["OrganizationCode"] == "IPU"
    assert stamped["OrganizationName"] == "Inter-Parliamentary Union"
    assert stamped["QueryCode"] == "SG.GEN.PARL.ZS"


@pytest.mark.parametrize(
    "org_folder, dataset_folder, indicator_code, collect_kwargs",
    [
        (
            "wgi", "wgi_pubsrv", "GOV_WGI_GE.EST",
            {
                "source": 3,
                "organization_code": "WGI",
                "organization_name": "World Bank - Worldwide Governance Indicators",
            },
        ),
        (
            "ipu", "ipu_wmplmt", "SG.GEN.PARL.ZS",
            {
                "organization_code": "IPU",
                "organization_name": "Inter-Parliamentary Union",
            },
        ),
        ("wb", "wb_taxrev", "GC.TAX.TOTL.GD.ZS", {}),
    ],
)
def test_should_stamp_source_info_matching_doc_source_when_collected(
    monkeypatch, org_folder, dataset_folder, indicator_code, collect_kwargs
):
    """Every key in the doc's Source becomes a Mongo filter against the raw
    document's Source, so the doc Source must be an exact subset of what the
    collector stamps."""
    captured = _install_fakes(monkeypatch)
    list(worldbank.collect_wb_data(indicator_code, username="tester", **collect_kwargs))
    stamped = captured["source_infos"][0]
    doc_source = _load_doc_source(org_folder, dataset_folder)
    assert doc_source, "doc Source must not be empty"
    for key, value in doc_source.items():
        assert value is not None, f"doc Source.{key} must not be null"
        assert key in stamped, f"doc Source.{key} not stamped on raw docs"
        assert stamped[key] == value, (
            f"doc Source.{key}={value!r} but collector stamps {stamped[key]!r}"
        )


def test_should_reject_stale_doc_source_shape_when_doc_has_bad_keys():
    """Guard against regressing to the old docs that carried null QueryCode
    and a BaseURL that no raw document would ever match."""
    for org_folder, dataset_folder in (("wgi", "wgi_pubsrv"), ("ipu", "ipu_wmplmt")):
        doc_source = _load_doc_source(org_folder, dataset_folder)
        assert set(doc_source.keys()) == {"OrganizationCode", "QueryCode"}
