from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
import json
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    score_single_indicator
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg,
    filter_sdg,
)


from sspi_flask_app.api.resources.utilities import goalpost
from bs4 import BeautifulSoup
import pycountry
from sspi_flask_app.api.datasource.worldbank import clean_wb_data
from sspi_flask_app.api.datasource.sipri import cleanSIPRIData
from flask import current_app as app


@compute_bp.route('/FORAID', methods=['GET'])
@login_required
def compute_foraid():
    app.logger.info("Running /api/v1/compute/FORAID")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FORAID"})

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
            aid_dict[donor_year] = {"donations": [],
                                    "receptions": [], "year": year, "cou": donor}
        if recipient_year not in aid_dict.keys():
            aid_dict[recipient_year] = {
                "donations": [], "receptions": [], "year": year, "cou": recipient}
        aid_dict[donor_year]["donations"].append(obs)
        aid_dict[recipient_year]["receptions"].append(obs)
    print("Computing ODA Totals")
    intermediates_list = []
    for cou_year, report in aid_dict.items():
        if not pycountry.countries.get(alpha_3=report["cou"]):
            continue
        intermediates_list.extend([{
            "CountryCode": report["cou"],
            "IntermediateCode": "TOTDON",
            "Year": report["year"],
            "Unit": "USD (Millions)",
            "Value": sum([float(d["Value"]) for d in report["donations"] if d.get("Value")]),
        }, {
            "CountryCode": report["cou"],
            "IntermediateCode": "TOTREC",
            "Year": report["year"],
            "Unit": "USD (Millions)",
            "Value": sum([float(d["Value"]) for d in report["receptions"] if d.get("Value")])
        }])
    print("Preparing Population Data")
    population_raw = sspi_raw_api_data.fetch_raw_data(
        "FORAID", IntermediateCode="POPULN")
    population_clean = clean_wb_data(population_raw, "FORAID", "Population")
    intermediates_list.extend(population_clean)
    print("Preparing GDP Data")
    gdp_raw = sspi_raw_api_data.fetch_raw_data(
        "FORAID", IntermediateCode="GDPMKT")
    gdp_clean = clean_wb_data(
        gdp_raw, "FORAID", "National GDP in 2015 Constant Dollars")
    intermediates_list.extend(gdp_clean)
    dlg = 0  # 0% of GDP Donated
    dug = 1  # 1% of GDP Donated
    rlg = 0  # 0 Dollars per Capita?
    rug = 500  # 500 Dollars per Capita?
    clean_list, incomplete_list = zip_intermediates(
        intermediates_list,
        "FORAID",
        ScoreFunction=lambda TOTDON, TOTREC, POPULN, GDPMKT: goalpost(
            TOTDON * 10**8 / GDPMKT, dlg, dug) if TOTDON > TOTREC else goalpost(
            TOTREC * 10**6 / POPULN, rlg, rug),
        ValueFunction=lambda TOTDON, TOTREC, POPULN, GDPMKT:
            TOTDON * 10**8 / GDPMKT if TOTDON > TOTREC else TOTREC * 10**6 / POPULN,
        UnitFunction=lambda TOTDON, TOTREC, POPULN, GDPMKT:
            "Donor: ODA Donations (% GDP)" if TOTDON > TOTREC else
            "Recipient: ODA Received per Capita (USD per Capita)",
        ScoreBy="Value")
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/MILEXP", methods=['GET'])
@login_required
def compute_milexp():
    app.logger.info("Running /api/v1/compute/MILEXP")
    sspi_clean_api_data.delete_many({"IndicatorCode": "MILEXP"})
    milexp_raw = sspi_raw_api_data.fetch_raw_data("MILEXP")
    cleaned_list = cleanSIPRIData(milexp_raw, 'MILEXP')
    obs_list = json.loads(cleaned_list.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "MILEXP")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/ARMEXP", methods=['GET'])
@login_required
def compute_armexp():
    app.logger.info("Running /api/v1/compute/ARMEXP")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ARMEXP"})
    # armexp_raw = sspi_raw_api_data.fetch_raw_data("ARMEXP")
    description = (
        "The supply of military weapons through sales, aid, gifts, and those "
        "made through manufacturing licenses."
    )
    cleaned_list = cleanSIPRIData(
        'local/armexp.csv',
        'ARMEXP',
        'Millions of arms',
        description
    ) 
    obs_list = json.loads(cleaned_list.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "ARMEXP")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/RDFUND", methods=['GET'])
@login_required
def compute_rdfund():
    """
    metadata_map = {
        "GB_XPD_RSDV": "GVTRDP",
        "GB_POP_SCIERD": "NRSRCH"
    }
    """
    app.logger.info("Running /api/v1/compute/RDFUND")
    sspi_clean_api_data.delete_many({"IndicatorCode": "RDFUND"})
    raw_data = sspi_raw_api_data.fetch_raw_data("RDFUND")
    watman_data = extract_sdg(raw_data)
    intermediate_map = {
        "GB_XPD_RSDV": "GVTRDP",
        "GB_POP_SCIERD": "NRSRCH"
    }
    intermediate_list = filter_sdg(
        watman_data, intermediate_map, activity="TOTAL"
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_list, "RDFUND",
        ScoreFunction=lambda GVTRDP, NRSRCH: (GVTRDP + NRSRCH) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
