"""
The download form must send every checked CountryGroup (SURFACES-6).

Evaluates DownloadForm.buildQueryParams from the unbundled source under plain
Node with a minimal fake form. Skips when node is not installed.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOWNLOAD_FORM_SOURCE = REPOSITORY_ROOT / "sspi_flask_app" / "client" / "static" / "js" / "download-form.js"
NODE_EXECUTABLE = shutil.which("node")

NODE_HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const [sourcePath, fieldsJson, countryType] = process.argv.slice(1);
const fields = JSON.parse(fieldsJson);
class FakeFormData {
    constructor(form) { this.fields = form.fields; }
    get(name) { const hit = this.fields.find(([key]) => key === name); return hit ? hit[1] : null; }
    getAll(name) { return this.fields.filter(([key]) => key === name).map(([, value]) => value); }
}
const fakeForm = {
    fields,
    querySelector(selector) {
        if (selector.includes('country-type')) { return { value: countryType }; }
        return null;
    },
};
const context = { FormData: FakeFormData, URLSearchParams, window: {}, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(sourcePath, 'utf8') + '\nthis.DownloadForm = DownloadForm;', context);
const form = Object.create(context.DownloadForm.prototype);
form.form = fakeForm;
const params = form.buildQueryParams();
process.stdout.write(JSON.stringify(Array.from(params.entries())));
"""


def build_query_params(fields, country_type="group"):
    result = subprocess.run(
        [NODE_EXECUTABLE, "-e", NODE_HARNESS, str(DOWNLOAD_FORM_SOURCE), json.dumps(fields), country_type],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


requires_node = pytest.mark.skipif(NODE_EXECUTABLE is None, reason="node is not installed")


@requires_node
def test_should_send_every_group_when_several_country_groups_are_checked():
    params = build_query_params([
        ["database", "sspi_item_data"],
        ["CountryGroup", "BRICS"],
        ["CountryGroup", "EU28"],
        ["Year", "2023"],
    ])
    assert [value for key, value in params if key == "CountryGroup"] == ["BRICS", "EU28"]


@requires_node
def test_should_send_no_group_when_individual_countries_are_selected():
    params = build_query_params([
        ["database", "sspi_item_data"],
        ["CountryGroup", "BRICS"],
        ["CountryCode", "USA"],
    ], country_type="individual")
    assert [key for key, _ in params if key == "CountryGroup"] == []
    assert ["CountryCode", "USA"] in params


@requires_node
def test_should_skip_empty_group_values_when_building_query():
    params = build_query_params([
        ["database", "sspi_item_data"],
        ["CountryGroup", ""],
        ["CountryGroup", "G20"],
    ])
    assert [value for key, value in params if key == "CountryGroup"] == ["G20"]
