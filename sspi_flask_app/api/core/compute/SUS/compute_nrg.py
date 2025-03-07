from flask import redirect, url_for
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

import pandas as pd
import json

from sspi_flask_app.api.datasource.iea import (
    cleanIEAData_altnrg,
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_airpol,
    flatten_nested_dictionary_nrgint,
)


@compute_bp.route("/AIRPOL")
@login_required
def compute_airpol():
    if not sspi_raw_api_data.raw_data_available("AIRPOL"):
        return redirect(url_for("api_bp.collect_bp.AIRPOL"))
    raw_data = sspi_raw_api_data.fetch_raw_data("AIRPOL")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    flattened = flatten_nested_dictionary_airpol(intermediate_obs_dict)
    scored_list = score_single_indicator(flattened, "AIRPOL")
    cleaned, filtered = filter_incomplete_data(scored_list)
    sspi_clean_api_data.insert_many(cleaned)
    print(filtered)
    return parse_json(cleaned)


@compute_bp.route("/NRGINT", methods=['GET'])
# @login_required
def compute_nrgint():
    if not sspi_raw_api_data.raw_data_available("NRGINT"):
        return redirect(url_for("collect_bp.NRGINT"))
    nrgint_raw = sspi_raw_api_data.fetch_raw_data("NRGINT")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(
        nrgint_raw)
    flattened_lst = flatten_nested_dictionary_nrgint(intermediate_obs_dict)
    scored_list = score_single_indicator(flattened_lst, "NRGINT")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)


@compute_bp.route("/ALTNRG", methods=['GET'])
@login_required
def compute_altnrg():
    if not sspi_raw_api_data.raw_data_available("ALTNRG"):
        return redirect(url_for("collect_bp.ALTNRG"))
    raw_data = sspi_raw_api_data.fetch_raw_data("ALTNRG")

    # most of these intermediates used to compute sum
    product_codes = {
        "COAL": "Coal",
        "NATGAS": "Natural gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro",
        "GEOTHERM": "Wind, solar, etc.",
        "COMRENEW": "Biofuels and waste",
        "MTOTOIL": "Oil"
    }

    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL"
    }

    intermediate_data = pd.DataFrame(cleanIEAData_altnrg(raw_data, "ALTNRG"))
    intermediate_data.drop(intermediate_data[intermediate_data["CountryCode"].map(
        lambda s: len(s) != 3)].index, inplace=True)
    intermediate_data["IntermediateCode"] = intermediate_data["IntermediateCode"].map(
        lambda x: metadata_code_map[x])
    intermediate_data.astype({"Year": "int", "Value": "float"})

    # adding sum of available intermediates as an intermediate, in order to complete data
    sums = intermediate_data.groupby(['Year', 'CountryCode']).agg({
        'Value': 'sum'}).reset_index()
    sums['IntermediateCode'], sums['Unit'], sums['IndicatorCode'] = 'TTLSUM', 'TJ', 'ALTNRG'

    # running the same operations for alternative energy sources
    inter_sums = intermediate_data[intermediate_data["IntermediateCode"].isin(
        ["HYDROP", "NCLEAR", "GEOPWR", "BIOWAS"])]
    alt_sums = inter_sums.groupby(['Year', 'CountryCode']).agg({
        'Value': 'sum'}).reset_index()
    alt_sums['IntermediateCode'], alt_sums['Unit'], alt_sums['IndicatorCode'] = 'ALTSUM', 'TJ', 'ALTNRG'

    intermediate_list = pd.concat(
        [pd.concat([intermediate_data, sums]), alt_sums])
    zipped_document_list = zip_intermediates(
        json.loads(str(intermediate_list.to_json(orient="records")),
                   parse_int=int, parse_float=float),
        "ALTNRG",
        ScoreFunction=lambda TTLSUM, ALTSUM, BIOWAS: (
            ALTSUM - 0.5 * BIOWAS)/(TTLSUM),
        ScoreBy="Values"
    )
    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    print(incomplete_observations)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)

