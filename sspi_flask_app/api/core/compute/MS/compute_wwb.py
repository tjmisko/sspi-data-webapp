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
    score_single_indicator
)

import pandas as pd
import json
from io import StringIO

from sspi_flask_app.api.datasource.oecdstat import (
    parse_oecd_observations
)
from bs4 import BeautifulSoup
import re
from datetime import datetime


@compute_bp.route("/SENIOR", methods=['GET'])
@login_required
def compute_senior():
    """
    metadata = raw_data[0]["Metadata"]
    metadata_soup = bs.BeautifulSoup(metadata, "lxml")
    to see the codes and their descriptions, uncomment and
    return the following two lines
    jsonify([[tag.get("value"), tag.get_text()]
             for tag in metadata_soup.find_all("code")])
    metadata_codes = {
        "PEN20A": "Expected years in retirement, men",
        "PEN20B": "Expected years in retirement, women",
        "PEN24A": "Old age income poverty, 66+",
    }
    """
    app.logger.info("Running /api/v1/compute/SENIOR")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SENIOR"})
    sspi_incomplete_api_data.delete_many({"IndicatorCode": "SENIOR"})

    def score_senior(SENLEF, SENLEM, SENCRF, SENCRM, SENPVT):
        YRSRTF = SENLEF - SENCRF
        YRSRTM = SENLEM - SENCRM
        lg_YRSRTF, ug_YRSRTF = 0, 20
        lg_YRSRTM, ug_YRSRTM = 0, 15
        lg_SENPVT, ug_SENPVT = 0, 50
        YRSRTF_score = goalpost(YRSRTF, lg_YRSRTF, ug_YRSRTF)
        YRSRTM_score = goalpost(YRSRTM, lg_YRSRTM, ug_YRSRTM)
        SENPVT_score = goalpost(SENPVT, lg_SENPVT, ug_SENPVT)
        return 0.25 * YRSRTM_score + 0.25 * YRSRTF_score + 0.50 * SENPVT_score,

    def build_metadata_map(metadata_xml):
        meta_string = metadata_xml.replace("\\r\\n", "\n")
        soup = BeautifulSoup(meta_string, "xml")
        code_name_map = {}
        for code in soup.find_all("Code"):
            code_id = code.get("id")
            name_tag = code.find("common:Name", {"xml:lang": "en"})
            if code_id and name_tag:
                code_name_map[code_id] = name_tag.get_text(strip=True)
        return code_name_map

    raw = sspi_raw_api_data.fetch_raw_data("SENIOR")
    meta_map = build_metadata_map(raw[0]["Metadata"][2:][:-1])
    intermediate_map = {
        "OAIP": {
            "F": "SENPVF",
            "M": "SENPVM",
            "_T": "SENPVT"
        },
        "LE": {
            "F": "SENLEF",
            "M": "SENLEM",
            "_T": "SENLET"
        },
        "CRPLF22": {
            "F": "SENCRF",
            "M": "SENCRM",
            "_T": "SENCRT"
        },
        "FRPLF22": {
            "F": "SENFRF",
            "M": "SENFRM",
            "_T": "SENFRT"
        },
        "PEP": {
            "_Z": "SENPEN",
        },
        "EIOP": {
            "_Z": "SENINC",
        }
    }

    obs_list = parse_oecd_observations(raw[0]["Raw"][2:][:-1])
    filtered_obs_list = []
    for obs in obs_list:
        if not bool(re.match(r'^[A-Z]{3}$', obs["REF_AREA"])):
            continue
        if not obs["MEASURE"] in ["OAIP", "RETIRE", "CRPLF22", "FRPLF22", "PEP", "EIOP", "LE"]:
            continue
        obs["CountryCode"] = obs["REF_AREA"]
        obs["Age"] = meta_map[obs["AGE"]]
        obs["Description"] = meta_map[obs["MEASURE"]]
        obs["Unit"] = meta_map[obs["UNIT_MEASURE"]]
        obs["ItemCode"] = intermediate_map[obs["MEASURE"]][obs["SEX"]]
        if obs["ItemCode"] in ["SENLEF", "SENLEM", "SENCRF", "SENCRM", "SENPVT"]:
            obs["IntermediateCode"] = obs["ItemCode"]
        if obs["ItemCode"] == "SENPVT" and obs["AGE"] != "Y_GE66":
            continue
        if obs["ItemCode"] in ["SENLEM", "SENLEF"] and obs["AGE"] != "BIRTH":
            continue
        obs["Value"] = float(obs["Value"])
        obs["Year"] = int(obs["Year"])
        current_year = datetime.now().year
        if obs["Year"] < 1990 or obs["Year"] > current_year:
            continue
        filtered_obs_list.append(obs)
    clean_list, incomplete_list = zip_intermediates(
        filtered_obs_list, "SENIOR",
        ScoreFunction=score_senior,
        ScoreBy="Value"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/FATINJ", methods=['GET'])
@login_required
def compute_fatinj():
    app.logger.info("Running /api/v1/compute/FATINJ")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FATINJ"})
    raw_data = sspi_raw_api_data.fetch_raw_data("FATINJ")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    fatinj_raw = pd.read_csv(csv_virtual_file)
    fatinj_raw = fatinj_raw[fatinj_raw["SEX"] == "SEX_T"]
    fatinj_raw = fatinj_raw[['REF_AREA',
                             'TIME_PERIOD',
                             'UNIT_MEASURE',
                             'OBS_VALUE']]
    fatinj_raw = fatinj_raw.rename(columns={'REF_AREA': 'CountryCode',
                                            'TIME_PERIOD': 'Year',
                                            'OBS_VALUE': 'Value',
                                            'UNIT_MEASURE': 'Unit'})
    fatinj_raw['IndicatorCode'] = 'FATINJ'
    fatinj_raw['Unit'] = 'Rate per 100,000'
    fatinj_raw.dropna(subset=['Value'], inplace=True)
    obs_list = json.loads(str(fatinj_raw.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "FATINJ")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
