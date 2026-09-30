"""
Unit tests for collect_sdg_indicator_data paging.

Production UNSDG_AIRPOL (indicator 11.6.2) held only page 1 of 3. The
collector must fetch every page, prove the fetched record count equals the
API's totalElements, and raise before writing anything when it cannot.
requests.get, time.sleep and sspi_raw_api_data.raw_insert_many are
monkeypatched; responses mimic the live PivotData shape
({"size", "totalElements", "totalPages", "pageNumber", "attributes",
"dimensions", "data"}).
"""
import re

import pytest
import requests

import sspi_flask_app.api.datasource.unsdg as unsdg


PAGE_URL_PATTERN = re.compile(r"indicator=(?P<code>[^&]+)&pageSize=(?P<size>\d+)&page=(?P<page>\d+)$")


def make_records(start, count):
    return [{"geoAreaCode": str(index), "series": "EN_ATM_PM25"} for index in range(start, start + count)]


def make_page(page_number, data, total_elements, total_pages, size=500):
    return {
        "size": size,
        "totalElements": total_elements,
        "totalPages": total_pages,
        "pageNumber": page_number,
        "attributes": [],
        "dimensions": [],
        "data": data,
    }


class FakeResponse:
    def __init__(self, payload=None, status_code=200, json_error=None):
        self.payload = payload
        self.status_code = status_code
        self.json_error = json_error

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Server Error")

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeSDGApi:
    """
    Serves responses keyed by page number. A page maps to a list of responses
    (or exceptions) consumed in order, so a retry can see a different result.
    """

    def __init__(self, responses_by_page):
        self.responses_by_page = {page: list(responses) for page, responses in responses_by_page.items()}
        self.requested_urls = []

    def get(self, url, timeout=None):
        self.requested_urls.append(url)
        match = PAGE_URL_PATTERN.search(url)
        assert match, f"collector requested an unpaged URL: {url}"
        assert timeout, "collector must pass a timeout"
        queue = self.responses_by_page.get(int(match.group("page")))
        assert queue, f"unexpected request for {url}"
        response = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def fake_environment(monkeypatch):
    inserted = []

    def _fake_raw_insert_many(document_list, source_info, **kwargs):
        inserted.append({"data": list(document_list), "source_info": dict(source_info), "kwargs": kwargs})
        return len(document_list)

    monkeypatch.setattr(unsdg.sspi_raw_api_data, "raw_insert_many", _fake_raw_insert_many)
    monkeypatch.setattr(unsdg.time, "sleep", lambda seconds: None)

    def install(responses_by_page):
        api = FakeSDGApi(responses_by_page)
        monkeypatch.setattr(unsdg.requests, "get", api.get)
        return api

    return install, inserted


def run_collector(code="11.6.2"):
    return list(unsdg.collect_sdg_indicator_data(code, username="tester"))


def test_should_insert_every_page_when_final_page_is_short(fake_environment):
    install, inserted = fake_environment
    api = install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 1292, 3))],
        2: [FakeResponse(make_page(2, make_records(500, 500), 1292, 3))],
        3: [FakeResponse(make_page(3, make_records(1000, 292), 1292, 3))],
    })
    messages = run_collector()
    assert [len(batch["data"]) for batch in inserted] == [500, 500, 292]
    assert [batch["source_info"]["URL"][-7:] for batch in inserted] == ["&page=1", "&page=2", "&page=3"]
    assert len(api.requested_urls) == 3
    assert "1292 of 1292" in messages[-1]


def test_should_keep_raw_source_info_shape_when_pages_are_inserted(fake_environment):
    install, inserted = fake_environment
    install({1: [FakeResponse(make_page(1, make_records(0, 2), 2, 1))]})
    run_collector("11.6.2")
    assert inserted[0]["source_info"] == {
        "OrganizationName": "United Nations Sustainable Development Goals",
        "OrganizationCode": "UNSDG",
        "OrganizationSeriesCode": "11.6.2",
        "QueryCode": "11.6.2",
        "BaseURL": "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/PivotData?indicator=11.6.2",
        "URL": "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/PivotData?indicator=11.6.2&pageSize=500&page=1",
    }
    assert inserted[0]["kwargs"] == {"username": "tester"}


def test_should_raise_and_insert_nothing_when_middle_page_is_empty(fake_environment):
    install, inserted = fake_environment
    install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 1292, 3))],
        2: [FakeResponse(make_page(2, [], 1292, 3))],
        3: [FakeResponse(make_page(3, make_records(1000, 292), 1292, 3))],
    })
    with pytest.raises(unsdg.SDGCollectionError, match="page 2 of 3 is empty"):
        run_collector()
    assert inserted == []


def test_should_raise_and_insert_nothing_when_first_page_is_empty_but_total_is_positive(fake_environment):
    install, inserted = fake_environment
    install({1: [FakeResponse(make_page(1, [], 10, 1))]})
    with pytest.raises(unsdg.SDGCollectionError, match="empty"):
        run_collector()
    assert inserted == []


def test_should_accept_trailing_empty_page_when_all_records_already_fetched(fake_environment):
    install, inserted = fake_environment
    install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 1000, 3))],
        2: [FakeResponse(make_page(2, make_records(500, 500), 1000, 3))],
        3: [FakeResponse(make_page(3, [], 1000, 3))],
    })
    run_collector()
    assert [len(batch["data"]) for batch in inserted] == [500, 500, 0]


def test_should_raise_and_insert_nothing_when_fetched_count_is_below_total_elements(fake_environment):
    install, inserted = fake_environment
    install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 1292, 3))],
        2: [FakeResponse(make_page(2, make_records(500, 500), 1292, 3))],
        3: [FakeResponse(make_page(3, make_records(1000, 200), 1292, 3))],
    })
    with pytest.raises(unsdg.SDGCollectionError, match="fetched 1200 records .* totalElements=1292"):
        run_collector()
    assert inserted == []


def test_should_raise_when_fetched_count_exceeds_total_elements(fake_environment):
    install, inserted = fake_environment
    install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 700, 2))],
        2: [FakeResponse(make_page(2, make_records(500, 500), 700, 2))],
    })
    with pytest.raises(unsdg.SDGCollectionError, match="fetched 1000"):
        run_collector()
    assert inserted == []


def test_should_raise_when_total_pages_cannot_hold_total_elements(fake_environment):
    install, inserted = fake_environment
    api = install({1: [FakeResponse(make_page(1, make_records(0, 500), 1292, 1))]})
    with pytest.raises(unsdg.SDGCollectionError, match="1 pages for 1292 records"):
        run_collector()
    assert inserted == []
    assert len(api.requested_urls) == 1


def test_should_raise_when_api_returns_same_page_for_every_page_request(fake_environment):
    install, inserted = fake_environment
    page_one = FakeResponse(make_page(1, make_records(0, 500), 1000, 2))
    install({1: [page_one], 2: [page_one]})
    with pytest.raises(unsdg.SDGCollectionError, match="pageNumber 1 when page 2"):
        run_collector()
    assert inserted == []


def test_should_raise_when_total_elements_changes_between_pages(fake_environment):
    install, inserted = fake_environment
    install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 1000, 2))],
        2: [FakeResponse(make_page(2, make_records(500, 501), 1001, 2))],
    })
    with pytest.raises(unsdg.SDGCollectionError, match="changed from 1000 to 1001"):
        run_collector()
    assert inserted == []


def test_should_raise_when_indicator_reports_zero_records(fake_environment):
    install, inserted = fake_environment
    install({1: [FakeResponse(make_page(1, [], 0, 0))]})
    with pytest.raises(unsdg.SDGCollectionError, match="no records"):
        run_collector()
    assert inserted == []


@pytest.mark.parametrize("payload", [
    {"data": []},
    {"totalElements": 10, "totalPages": 1},
    {"totalElements": "10", "totalPages": 1, "data": []},
    {"totalElements": 10, "totalPages": None, "data": []},
    {"totalElements": True, "totalPages": 1, "data": []},
    {"totalElements": -1, "totalPages": 1, "data": []},
    ["not", "a", "dict"],
    None,
])
def test_should_raise_and_insert_nothing_when_response_lacks_paging_fields(fake_environment, payload):
    install, inserted = fake_environment
    install({1: [FakeResponse(payload)]})
    with pytest.raises(unsdg.SDGCollectionError):
        run_collector()
    assert inserted == []


def test_should_retry_page_when_request_fails_transiently(fake_environment):
    install, inserted = fake_environment
    api = install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 800, 2))],
        2: [
            requests.ConnectionError("reset by peer"),
            FakeResponse(status_code=503),
            FakeResponse(make_page(2, make_records(500, 300), 800, 2)),
        ],
    })
    run_collector()
    assert [len(batch["data"]) for batch in inserted] == [500, 300]
    assert len(api.requested_urls) == 4


def test_should_raise_and_insert_nothing_when_page_fails_every_attempt(fake_environment):
    install, inserted = fake_environment
    api = install({
        1: [FakeResponse(make_page(1, make_records(0, 500), 800, 2))],
        2: [FakeResponse(json_error=ValueError("Expecting value: line 1 column 1"))],
    })
    with pytest.raises(unsdg.SDGCollectionError, match="failed after 3 attempts"):
        run_collector()
    assert inserted == []
    assert len(api.requested_urls) == 1 + unsdg.SDG_PIVOT_PAGE_MAX_ATTEMPTS


def test_should_log_error_when_collection_is_incomplete(fake_environment, caplog):
    install, _ = fake_environment
    install({1: [FakeResponse(make_page(1, make_records(0, 400), 500, 1))]})
    with caplog.at_level("ERROR", logger=unsdg.__name__):
        with pytest.raises(unsdg.SDGCollectionError):
            run_collector()
    assert any("totalElements=500" in record.getMessage() for record in caplog.records)
