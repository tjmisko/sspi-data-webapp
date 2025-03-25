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
import pycountry


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
    # Metadata was not necessary because all flows were type 206 (ODA)
    # def build_metadata_map(metadata_xml):
    #     meta_string = raw[0]["Metadata"][2:][:-1]
    #     meta_string = meta_string.replace("\\r\\n", "\n")
    #     soup = BeautifulSoup(metadata_xml, "xml")
    #     return soup
    # meta_soup = build_metadata_map(raw[0]["Metadata"])
    raw = sspi_raw_api_data.fetch_raw_data("FORAID", IntermediateCode="ODAFLW")
    raw_data_combined = []
    for i, r in enumerate(raw):
        print(f"Extracting Raw Data for XML Object {i} of {len(raw)}")
        obs = parse_observations(r["Raw"][2:][:-1])
        raw_data_combined.extend(obs)
    print("Constructing Tally")
    aid_dict = {}
    for obs in raw_data_combined:
        donor = obs["DONOR"]
        recipient = obs["RECIPIENT"]
        year = obs["Year"]
        donor_year = f"{donor}_{year}"
        recipient_year = f"{recipient}_{year}"
        if donor_year not in aid_dict.keys():
            aid_dict[donor_year] = {"donations": [], "receptions": [], "year": year, "cou": donor}
        if recipient_year not in aid_dict.keys():
            aid_dict[recipient_year] = {"donations": [], "receptions": [], "year": year, "cou": recipient}
        aid_dict[donor_year]["donations"].append(obs)
        aid_dict[recipient_year]["receptions"].append(obs)
    print("Computing ODA Totals")
    aid_totals = []
    for cou_year, report in aid_dict.items():
        if not pycountry.countries.get(alpha_3=report["cou"]):
            continue
        aid_totals.append({
            "CountryCode": report["cou"],
            "Year": report["year"],
            "TotalDonations": sum([float(d["Value"]) for d in report["donations"] if d.get("Value")]),
            "TotalReceptions": sum([float(d["Value"]) for d in report["receptions"] if d.get("Value")])
        })
    print("Sorting Receivers and Donors")
    for obs in aid_totals:
        if obs["TotalDonations"] > obs["TotalReceptions"]:
            obs["CountryType"] = "Donor"
        else:
            obs["CountryType"] = "Recipient"


    return parse_json(aid_totals)
