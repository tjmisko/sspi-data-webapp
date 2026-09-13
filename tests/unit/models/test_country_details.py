import json
from collections import Counter
from pathlib import Path

import pytest

from sspi_flask_app.models.database.sspi_metadata import SSPIMetadata

COUNTRY_GROUPS_PATH = Path(__file__).resolve().parents[3] / "local" / "country-groups.json"


@pytest.fixture(scope="module")
def country_groups():
    with open(COUNTRY_GROUPS_PATH) as file:
        return json.load(file)


@pytest.fixture(scope="module")
def country_details(country_groups):
    # build_country_details does not touch the database, so no instance state is needed.
    return SSPIMetadata.build_country_details(None, country_groups)


def details_by_code(country_details):
    return {detail["Metadata"]["CountryCode"]: detail["Metadata"] for detail in country_details}


def test_should_emit_one_detail_per_code_when_codes_repeat_across_groups(country_details):
    counts = Counter(detail["Metadata"]["CountryCode"] for detail in country_details)
    duplicated = {code: n for code, n in counts.items() if n > 1}
    assert not duplicated


def test_should_emit_a_named_flagged_detail_for_every_index_country(country_groups, country_details):
    by_code = details_by_code(country_details)
    missing = [code for code in country_groups["SSPI67"] if code not in by_code]
    assert not missing, f"Index countries silently dropped from CountryDetail: {missing}"
    for code in country_groups["SSPI67"]:
        assert by_code[code]["Country"], f"{code} has an empty country name"
        assert by_code[code]["Flag"], f"{code} has an empty flag"


def test_should_include_turkiye_in_its_groups_when_named_turkiye_upstream(country_details):
    turkiye = details_by_code(country_details)["TUR"]
    assert {"SSPI49", "SSPI67", "G20", "OECD"} <= set(turkiye["CountryGroups"])


def test_should_list_every_sspi49_country_when_directory_renders(country_groups, country_details):
    sspi49_codes = {code for code, meta in details_by_code(country_details).items() if "SSPI49" in meta["CountryGroups"]}
    assert sspi49_codes == set(country_groups["SSPI49"])
    assert len(sspi49_codes) == 49


def test_should_skip_codes_unknown_to_pycountry_instead_of_emitting_blank_details():
    details = SSPIMetadata.build_country_details(None, {"Fake": ["TUR", "ZZZ", ""]})
    assert [detail["Metadata"]["CountryCode"] for detail in details] == ["TUR"]
