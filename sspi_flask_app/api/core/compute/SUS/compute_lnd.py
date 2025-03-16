from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.datasource.fao import format_FAO_data_series
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)

import pandas as pd
import json
import re
from io import StringIO

from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_watman,
    flatten_nested_dictionary_stkhlm,
)


@compute_bp.route("/NITROG", methods=['GET'])
@login_required
def compute_nitrog():
    if not sspi_raw_api_data.raw_data_available("NITROG"):
        return redirect(url_for("collect_bp.NITROG"))
    raw_data = sspi_raw_api_data.fetch_raw_data("NITROG")
    csv_virtual_file = StringIO(raw_data[0]["Raw"]["csv"])
    SNM_raw = pd.read_csv(csv_virtual_file)
    SNM_raw = SNM_raw.drop(columns=['code', 'country'])
    SNM_raw = SNM_raw.rename(columns={'iso': 'CountryCode'})
    SNM_long = SNM_raw.melt(
        id_vars=['CountryCode'],
        var_name='YearString',
        value_name='Value'
    )
    SNM_long["Year"] = [
        re.search(r"\d{4}", s).group(0)
        for s in SNM_long["YearString"]
    ]
    SNM_long.drop(columns=['YearString'], inplace=True)
    SNM_long.drop(SNM_long[SNM_long['Value'] < 0].index, inplace=True)
    SNM_long.drop(SNM_long[SNM_long['Value'].isna()].index, inplace=True)
    SNM_long['IndicatorCode'] = 'NITROG'
    SNM_long['Unit'] = 'Index'
    obs_list = json.loads(SNM_long.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "NITROG")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/WATMAN", methods=['GET'])
@login_required
def compute_watman():
    """
    metadata_map = {
        "ER_H2O_WUEYST": "CWUEFF",
        "ER_H2O_STRESS": "WTSTRS"
    }
    """
    if not sspi_raw_api_data.raw_data_available("WATMAN"):
        return redirect(url_for("collect_bp.WATMAN"))
    raw_data = sspi_raw_api_data.fetch_raw_data("WATMAN")
    total_list = [obs for obs in raw_data if obs["Raw"]["activity"] == "TOTAL"]
    intermediate_list = extract_sdg_pivot_data_to_nested_dictionary(total_list)
    final_list = flatten_nested_dictionary_watman(intermediate_list)
    zipped_document_list = zip_intermediates(final_list, "WATMAN",
                                             ScoreFunction=lambda CWUEFF, WTSTRS: 0.50 * CWUEFF + 0.50 * WTSTRS,
                                             ScoreBy="Score")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)


@compute_bp.route("/STKHLM", methods=['GET'])
@login_required
def compute_stkhlm():
    if not sspi_raw_api_data.raw_data_available("STKHLM"):
        return redirect(url_for("api_bp.collect_bp.STKHLM"))
    raw_data = sspi_raw_api_data.fetch_raw_data("STKHLM")
    full_stk_list = [obs for obs in raw_data if obs["Raw"]
                     ["series"] == "SG_HAZ_CMRSTHOLM"]
    intermediate_list = extract_sdg_pivot_data_to_nested_dictionary(
        full_stk_list)
    flattened_lst = flatten_nested_dictionary_stkhlm(intermediate_list)
    scored_list = score_single_indicator(flattened_lst, "STKHLM")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)


@compute_bp.route("/DEFRST", methods=['GET'])
@login_required
def compute_defrst():
    if not sspi_raw_api_data.raw_data_available("DEFRST"):
        return redirect(url_for("collect_bp.DEFRST"))
    indicator_detail = sspi_metadata.get_detail("DEFRST")
    lg = indicator_detail["Metadata"]["LowerGoalpost"]
    ug = indicator_detail["Metadata"]["UpperGoalpost"]
    raw_data = sspi_raw_api_data.fetch_raw_data("DEFRST")[0]["Raw"]["data"]
    clean_obs_list = format_FAO_data_series(raw_data, "DEFRST")
    average_1990s_dict = {}
    for obs in clean_obs_list:
        if obs["Year"] not in list(range(1990, 2000)):
            continue
        if obs["CountryCode"] not in average_1990s_dict.keys():
            average_1990s_dict[obs["CountryCode"]] = {"Values": []}
        average_1990s_dict[obs["CountryCode"]]["Values"].append(obs["Value"])
    for country in average_1990s_dict.keys():
        sum_1990s = sum(average_1990s_dict[country]["Values"])
        len_1990s = len(average_1990s_dict[country]["Values"])
        average_1990s_dict[country]["Average"] = sum_1990s / len_1990s
    final_data_list = []
    for obs in clean_obs_list:
        if obs["Year"] in list(range(1900, 2000)):
            continue
        if obs["CountryCode"] not in average_1990s_dict.keys():
            continue
        if obs["Value"] == 0:
            obs["Score"] = 0
        if average_1990s_dict[obs["CountryCode"]]["Average"] == 0:
            continue
        lv = obs["Value"]
        av = average_1990s_dict[obs["CountryCode"]]["Average"]
        final_data_list.append({
            "IndicatorCode": "DEFRST",
            "CountryCode": obs["CountryCode"],
            "Year": obs["Year"],
            "Value": (lv - av) / av * 100,
            "Score": goalpost((lv - av) / av * 100, lg, ug),
            "LowerGoalpost": lg,
            "UpperGoalpost": ug,
            "Unit": "Percentage Change in Forest Cover from 1990s Average",
            "Intermediates": [
                {
                    "IntermediateCode": "FRSTLV",
                    "CountryCode": obs["CountryCode"],
                    "Year": obs["Year"],
                    "Value": lv,
                    "Unit": obs["Unit"]
                },
                {
                    "IntermediateCode": "FRSTAV",
                    "CountryCode": obs["CountryCode"],
                    "Year": obs["Year"],
                    "Value": average_1990s_dict[obs["CountryCode"]]["Average"],
                    "Unit": obs["Unit"] + " (1990s Average)"
                }
            ]
        })
    sspi_clean_api_data.insert_many(final_data_list)
    return parse_json(final_data_list)


@compute_bp.route("/CARBON", methods=['GET'])
@login_required
def compute_carbon():
    if not sspi_raw_api_data.raw_data_available("CARBON"):
        return redirect(url_for("collect_bp.DEFRST"))
    indicator_detail = sspi_metadata.get_detail("CARBON")
    lg = indicator_detail["Metadata"]["LowerGoalpost"]
    ug = indicator_detail["Metadata"]["UpperGoalpost"]
    raw_data = sspi_raw_api_data.fetch_raw_data("CARBON")[0]["Raw"]["data"]
    clean_obs_list = format_FAO_data_series(raw_data, "CARBON")
    average_1990s_dict = {}
    for obs in clean_obs_list:
        if obs["Year"] not in list(range(1990, 2000)):
            continue
        if obs["CountryCode"] not in average_1990s_dict.keys():
            average_1990s_dict[obs["CountryCode"]] = {"Values": []}
        average_1990s_dict[obs["CountryCode"]]["Values"].append(obs["Value"])
    for country in average_1990s_dict.keys():
        sum_1990s = sum(average_1990s_dict[country]["Values"])
        len_1990s = len(average_1990s_dict[country]["Values"])
        average_1990s_dict[country]["Average"] = sum_1990s / len_1990s
    final_data_list = []
    for obs in clean_obs_list:
        if obs["Year"] in list(range(1900, 2000)):
            continue
        if obs["CountryCode"] not in average_1990s_dict.keys():
            continue
        if obs["Value"] == 0:
            obs["Score"] = 0
        if average_1990s_dict[obs["CountryCode"]]["Average"] == 0:
            continue
        lv = obs["Value"]
        av = average_1990s_dict[obs["CountryCode"]]["Average"]
        final_data_list.append({
            "IndicatorCode": "CARBON",
            "CountryCode": obs["CountryCode"],
            "Year": obs["Year"],
            "Value": (lv - av) / av * 100,
            "Score": goalpost((lv - av) / av * 100, lg, ug),
            "LowerGoalpost": lg,
            "UpperGoalpost": ug,
            "Unit": "Percentage Change in Carbon Stock in Living Biomass from 1990s Average",
            "Intermediates": [
                {
                    "IntermediateCode": "CRBNLV",
                    "CountryCode": obs["CountryCode"],
                    "Year": obs["Year"],
                    "Value": lv,
                    "Unit": obs["Unit"]
                },
                {
                    "IntermediateCode": "CRBNAV",
                    "CountryCode": obs["CountryCode"],
                    "Year": obs["Year"],
                    "Value": average_1990s_dict[obs["CountryCode"]]["Average"],
                    "Unit": obs["Unit"] + " (1990s Average)"
                }
            ]
        })
    sspi_clean_api_data.insert_many(final_data_list)
    return parse_json(final_data_list)
