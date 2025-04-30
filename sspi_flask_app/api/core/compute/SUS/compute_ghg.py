from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    zip_intermediates,
)
from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)
from sspi_flask_app.api.datasource.iea import (
    cleanIEAData_altnrg,
    clean_IEA_data_GTRANS
)
import pandas as pd
import json
import jq


@compute_bp.route("/COALPW", methods=['GET'])
@login_required
def compute_coalpw():
    """
    product_codes = {
        "COAL": "Coal",
        "NATGAS": "Natural gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro",
        "GEOTHERM": "Wind, solar, etc.",
        "COMRENEW": "Biofuels and waste",
        "MTOTOIL": "Oil"
    }
    """
    app.logger.info("Running /api/v1/compute/COALPW")
    sspi_clean_api_data.delete_many({"IndicatorCode": "COALPW"})
    raw_data = sspi_raw_api_data.fetch_raw_data("COALPW")
    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL"
    }
    intermediate_data = pd.DataFrame(cleanIEAData_altnrg(raw_data, "COALPW"))
    intermediate_data.drop(intermediate_data[intermediate_data["CountryCode"].map(
        lambda s: len(s) != 3)].index, inplace=True)
    intermediate_data["IntermediateCode"] = intermediate_data["IntermediateCode"].map(
        lambda x: metadata_code_map[x])
    intermediate_data.astype({"Year": "int", "Value": "float"})
    # adding sum of available intermediates as an intermediate, in order to complete data
    sums = intermediate_data.groupby(['Year', 'CountryCode']).agg({
        'Value': 'sum'}).reset_index()
    sums['IntermediateCode'], sums['Unit'], sums['IndicatorCode'] = 'TTLSUM', 'TJ', 'COALPW'
    intermediate_list = pd.concat([intermediate_data, sums])
    intermediate_document_list = json.loads(
        str(intermediate_list.to_json(orient="records")), parse_int=int, parse_float=float
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_document_list,
        "COALPW",
        ScoreFunction=lambda TLCOAL, TTLSUM: (TLCOAL)/(TTLSUM),
        ScoreBy="Value"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/GTRANS", methods=['GET'])
@login_required
def compute_gtrans():
    app.logger.info("Running /api/v1/compute/GTRANS")
    sspi_clean_api_data.delete_many({"IndicatorCode": "GTRANS"})
    lg = 7500
    ug = 0
    pop_data = sspi_raw_api_data.fetch_raw_data(
        "GTRANS", IntermediateCode="POPULN")
    cleaned_pop = clean_wb_data(pop_data, "GTRANS", "Population")
    gtrans = sspi_raw_api_data.fetch_raw_data(
        "GTRANS", IntermediateCode="TCO2EQ"
    )
    cleaned_co2 = clean_IEA_data_GTRANS(
        gtrans, "GTRANS", "CO2 from transport sources"
    )
    document_list = cleaned_pop + cleaned_co2
    clean_list, incomplete_list = zip_intermediates(
        document_list,
        "GTRANS",
        ScoreFunction=lambda TCO2EQ, POPULN: goalpost(TCO2EQ / POPULN, lg, ug),
        ValueFunction=lambda TCO2EQ, POPULN: TCO2EQ / POPULN,
        ScoreBy="Value"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/BEEFMK", methods=['GET'])
@login_required
def compute_beefmk():
    app.logger.info("Running /api/v1/compute/BEEFMK")
    sspi_clean_api_data.delete_many({"IndicatorCode": "BEEFMK"})
    prod_lg, prod_ug = 50, 0
    cons_lg, cons_ug = 50, 0

    def score_beefmk(BFPROD, BFCONS, POPULN):
        prod_per_cap = BFPROD / POPULN
        score_prod = goalpost(prod_per_cap, prod_lg, prod_ug)
        score_cons = goalpost(BFCONS, cons_lg, cons_ug)
        return (score_prod + score_cons) / 2

    raw_data = sspi_raw_api_data.fetch_raw_data("BEEFMK", SourceOrganization="UNFAO")
    # return parse_json(jq.compile('.[].Raw.data.[]').input(raw_data).all())
    jq_filter = (
        '.[].Raw.data.[] | select( '
        '.Element == "Production" or '
        '.Element == "Food supply quantity (kg/capita/yr)" or '
        '.Element == "Total Population - Both sexes") | '
        'select(."Area Code (ISO3)" | length == 3) | '
        'select(."Area Code (ISO3)" | test("^[A-Z]{3}$"))'
    )
    all_observations = jq.compile(jq_filter).input(raw_data).all()
    jq_transform = (
        '.[] | {'
        'IndicatorCode: "BEEFMK", '
        'CountryCode: ."Area Code (ISO3)", '
        'Year: (.Year | tonumber), '
        'Value: (.Value | tonumber), '
        'Unit: .Unit, '
        'IntermediateCode: .Element,'
        'UNFAOFlag: ."Flag Description"'
        '}'
    )
    intermediates_list = jq.compile(jq_transform).input(all_observations).all()
    intermediate_map = {
        "Production": "BFPROD",
        "Food supply quantity (kg/capita/yr)": "BFCONS",
        "Total Population - Both sexes": "POPULN"
    }
    for obs in intermediates_list:
        obs["IntermediateCode"] = intermediate_map[obs["IntermediateCode"]]
        if obs["IntermediateCode"] == "BFPROD":
            obs["Value"] = obs["Value"] * 1E6
            obs["Unit"] = "kg"
        elif obs["IntermediateCode"] == "POPULN":
            obs["Value"] = obs["Value"] * 1E3
            obs["Unit"] = "Persons"
    clean_list, incomplete_list = zip_intermediates(
        intermediates_list,
        "BEEFMK",
        ScoreFunction=score_beefmk,
        ScoreBy="Value"
    )
    sspi_incomplete_api_data.insert_many(incomplete_list)
    sspi_clean_api_data.insert_many(clean_list)
    return parse_json(clean_list)
