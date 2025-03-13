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
        print("String start:", metadata_xml[0:150])
        print("String end:", metadata_xml[-150:])
        soup = BeautifulSoup(metadata_xml, "xml")
        print(soup.prettify())
        return metadata_xml

    raw = sspi_raw_api_data.fetch_raw_data("FORAID")
    # raw_data_combined = []
    # for r in raw:
    #     obs = parse_observations(r["Raw"][2:][:-1])
    #     raw_data_combined.extend(obs)
    metadata_map = build_metadata_map(raw[0]["Raw"][2:][:-1])
    return parse_json(raw[0])
