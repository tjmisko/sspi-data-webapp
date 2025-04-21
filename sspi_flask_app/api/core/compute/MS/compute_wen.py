from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    jsonify_df,
    parse_json,
    score_single_indicator
)

from sspi_flask_app.api.datasource.uis import (
    cleanUISdata
)
import pandas as pd
import json
from io import StringIO


@compute_bp.route("/EMPLOY", methods=['GET'])
@login_required
def compute_employ():
    app.logger.info("Running /api/v1/compute/EMPLOY")
    sspi_clean_api_data.delete_many({"IndicatorCode": "EMPLOY"})
    raw_data = sspi_raw_api_data.fetch_raw_data("EMPLOY")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    employ_raw = pd.read_csv(csv_virtual_file)
    employ_raw_f = employ_raw[['REF_AREA', 'TIME_PERIOD', 'MEASURE', 'SEX', 'UNIT_MEASURE', 'OBS_VALUE']]
    colmap_rename = {
        'REF_AREA': 'CountryCode',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value',
        'UNIT_MEASURE': 'Unit'
    }
    employ_raw_f = employ_raw_f[employ_raw_f['SEX'] == 'SEX_T']
    employ_raw_f = employ_raw_f.rename(columns=colmap_rename)
    employ_raw_f['IndicatorCode'] = 'EMPLOY'
    employ_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(employ_raw_f.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "EMPLOY")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/UNEMPL", methods=['GET'])
@login_required
def compute_unempl():
    app.logger.info("Running /api/v1/compute/UNEMPL")
    sspi_clean_api_data.delete_many({"IndicatorCode": "UNEMPL"})
    raw_data = sspi_raw_api_data.fetch_raw_data("UNEMPL")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    unempl_raw = pd.read_csv(csv_virtual_file)
    unempl_raw_f = unempl_raw[unempl_raw['SOC'] == 'SOC_CONTIG_UNE']
    unempl_raw_f = unempl_raw_f[['REF_AREA', 'TIME_PERIOD', 'UNIT_MEASURE', 'OBS_VALUE']]
    colmap_rename = {
        'REF_AREA': 'CountryCode',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value',
        'UNIT_MEASURE': 'Unit'
    }
    unempl_raw_f = unempl_raw_f.rename(columns=colmap_rename)
    unempl_raw_f['IndicatorCode'] = 'UNEMPL'
    unempl_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(unempl_raw_f.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "UNEMPL")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/COLBAR", methods=['GET'])
@login_required
def compute_colbar():
    app.logger.info("Running /api/v1/compute/COLBAR")
    sspi_clean_api_data.delete_many({"IndicatorCode": "COLBAR"})
    raw_data = sspi_raw_api_data.fetch_raw_data("COLBAR")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    colbar_raw = pd.read_csv(csv_virtual_file)
    colbar_raw = colbar_raw[['REF_AREA', 'TIME_PERIOD', 'UNIT_MEASURE',
                             'OBS_VALUE']]
    colbar_raw = colbar_raw.rename(columns={'REF_AREA': 'CountryCode',
                                            'TIME_PERIOD': 'Year',
                                            'OBS_VALUE': 'Value',
                                            'UNIT_MEASURE': 'Unit'})
    colbar_raw['IndicatorCode'] = 'COLBAR'
    colbar_raw['Unit'] = 'Proportion'
    colbar_raw['Value'] = colbar_raw['Value']
    obs_list = json.loads(colbar_raw.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "COLBAR")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/YRSEDU", methods=['GET'])
@login_required
def compute_yrsedu():
    if not sspi_raw_api_data.raw_data_available("YRSEDU"):
        return redirect(url_for("api_bp.collect_bp.YRSEDU"))
    raw_data = sspi_raw_api_data.fetch_raw_data("YRSEDU")
    cleaned_list = cleanUISdata(raw_data, "YRSEDU", "Years", "Number of years of compulsory primary and secondary education guaranteed in legal frameworks")
    scored_list = score_single_indicator(cleaned_list, "YRSEDU")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored_list)
    #sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)