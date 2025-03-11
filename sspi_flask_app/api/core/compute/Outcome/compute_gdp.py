from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_outcome_data,
    sspi_clean_outcome_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
)


@compute_bp.route("/outcome/GDPMER", methods=['GET'])
@login_required
def compute_gdpmer():
    if not sspi_raw_outcome_data.raw_data_available("GDPMER"):
        return "No Data for GDPMER found in raw database! Try running collect."
    gdpmer_raw = sspi_raw_outcome_data.fetch_raw_data("GDPMER")
    extracted_data = []
    for obs in gdpmer_raw:
        value = obs["Raw"]["value"]
        if not value or value == "None" or value == "null":
            continue
        if not len(obs["Raw"]["countryiso3code"]) == 3:
            continue
        extracted_data.append({
            "CountryCode": obs["Raw"]["countryiso3code"],
            "IndicatorCode": "GDPMER",
            "Year": int(obs["Raw"]["date"]),
            "Value": float(obs["Raw"]["value"]),
            "Unit": obs["Raw"]["indicator"]["value"],
            "Score": float(obs["Raw"]["value"])
        })
    sspi_clean_outcome_data.insert_many(extracted_data)
    return parse_json(extracted_data)


@compute_bp.route("/outcome/GDPPPP", methods=['GET'])
@login_required
def compute_gdpppp():
    if not sspi_raw_outcome_data.raw_data_available("GDPPPP"):
        return "No Data for GDPPPP found in raw database! Try running collect."
    gdpppp_raw = sspi_raw_outcome_data.fetch_raw_data("GDPPPP")
    extracted_data = []
    for obs in gdpppp_raw:
        value = obs["Raw"]["value"]
        if not value or value == "None" or value == "null":
            continue
        if not len(obs["Raw"]["countryiso3code"]) == 3:
            continue
        extracted_data.append({
            "CountryCode": obs["Raw"]["countryiso3code"],
            "IndicatorCode": "GDPPPP",
            "Year": int(obs["Raw"]["date"]),
            "Value": float(obs["Raw"]["value"]),
            "Unit": obs["Raw"]["indicator"]["value"],
            "Score": float(obs["Raw"]["value"])
        })
    sspi_clean_outcome_data.insert_many(extracted_data)
    return parse_json(extracted_data)

@compute_bp.route("/outcome/COTRAN", methods=['GET'])
@login_required
def compute_gtrans():
    pop_data = sspi_raw_api_data.fetch_raw_data("GTRANS", IntermediateCode = "UNPOPL")
    cleaned_pop = clean_wb_data(pop_data, "GTRANS", "Population")
    gtrans = sspi_raw_api_data.fetch_raw_data("GTRANS", IntermediateCode = "TCO2EQ")
    cleaned_co2 = clean_IEA_data_GTRANS(gtrans, "GTRANS", "CO2 from transport sources")
    document_list = cleaned_pop + cleaned_co2
    scored = zip_intermediates(document_list, "GTRANS", 
                               ScoreFunction = lambda TCO2EQ, UNPOPL: TCO2EQ / UNPOPL, ScoreBy = "Values")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)
