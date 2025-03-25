from flask import redirect, url_for, jsonify
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)
from bs4 import BeautifulSoup


@compute_bp.route('/FORAID', methods=['GET'])
@login_required
def compute_foraid():
    def parse_observations(xml_string) -> list[dict]:
        soup = BeautifulSoup(xml_string, "lxml-xml")
        observations = soup.find_all("Obs")
        formatted_observations = []
        for obs in observations:
            formatted_obs = {}
            value = obs.find("ObsValue")
            if value:
                formatted_obs["Value"] = value.attrs.get("value")
            for value in obs.find_all("Value"):
                id = value.attrs.get("id")
                if id == "TIME_PERIOD":
                    formatted_obs["Year"] = value.attrs.get("value")
                else:
                    formatted_obs[id] = value.attrs.get("value")
            formatted_observations.append(formatted_obs)
        return formatted_observations

    def build_metadata_map(metadata_xml):
        meta_string = raw[0]["Metadata"][2:][:-1]
        meta_string = meta_string.replace("\\r\\n", "\n")
        soup = BeautifulSoup(metadata_xml, "xml")
        return soup

    raw = sspi_raw_api_data.fetch_raw_data("FORAID")
    raw_data_combined = []
    for r in raw:
        obs = parse_observations(r["Raw"][2:][:-1])
        raw_data_combined.extend(obs)
    meta_soup = build_metadata_map(raw[0]["Metadata"])
    return parse_json(raw_data_combined)
