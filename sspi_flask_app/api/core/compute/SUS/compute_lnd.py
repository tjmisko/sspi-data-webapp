from flask import current_app as app
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
    score_single_indicator
)

import pandas as pd
import json
import re
from io import StringIO

from sspi_flask_app.api.datasource.sdg import (
    extract_sdg,
    filter_sdg,
)


@compute_bp.route("/NITROG", methods=['GET'])
@login_required
def compute_nitrog():
    app.logger.info("Running /api/v1/compute/NITROG")
    sspi_clean_api_data.delete_many({"IndicatorCode": "NITROG"})
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
    app.logger.info("Running /api/v1/compute/WATMAN")
    sspi_clean_api_data.delete_many({"IndicatorCode": "WATMAN"})
    raw_data = sspi_raw_api_data.fetch_raw_data("WATMAN")
    watman_data = extract_sdg(raw_data)
    intermediate_map = {
        "ER_H2O_WUEYST": "CWUEFF",
        "ER_H2O_STRESS": "WTSTRS"
    }
    intermediate_list = filter_sdg(
        watman_data, intermediate_map, activity="TOTAL"
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_list, "WATMAN",
        ScoreFunction=lambda CWUEFF, WTSTRS: (CWUEFF + WTSTRS) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    print(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/STKHLM", methods=['GET'])
@login_required
def compute_stkhlm():
    app.logger.info("Running /api/v1/compute/STKHLM")
    sspi_clean_api_data.delete_many({"IndicatorCode": "STKHLM"})
    raw_data = sspi_raw_api_data.fetch_raw_data("STKHLM")
    extracted_stkhlm = extract_sdg(raw_data)
    filtered_stkhlm = filter_sdg(
        extracted_stkhlm, {"SG_HAZ_CMRSTHOLM": "STKHLM"},
    )
    scored_list = score_single_indicator(filtered_stkhlm, "STKHLM")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/DEFRST", methods=['GET'])
@login_required
def compute_defrst():
    app.logger.info("Running /api/v1/compute/DEFRST")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DEFRST"})
    lg, ug = sspi_metadata.get_goalposts("DEFRST")
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
    app.logger.info("Running /api/v1/compute/CARBON")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CARBON"})
    lg, ug = sspi_metadata.get_goalposts("CARBON")
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
