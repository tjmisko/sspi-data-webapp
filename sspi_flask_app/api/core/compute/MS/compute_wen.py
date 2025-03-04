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
from io import StringIO


@compute_bp.route("/UNEMPL", methods=['GET'])
@login_required
def compute_unempl():
    if not sspi_raw_api_data.raw_data_available("UNEMPL"):
        return redirect(url_for("collect_bp.UNEMPL"))
    raw_data = sspi_raw_api_data.fetch_raw_data("UNEMPL")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    colbar_raw = pd.read_csv(csv_virtual_file)
    colbar_raw_f = colbar_raw[colbar_raw['SOC'] == 'SOC_CONTIG_UNE']
    colbar_raw_f = colbar_raw_f[['REF_AREA',
                                 'TIME_PERIOD', 'UNIT_MEASURE', 'OBS_VALUE']]
    colbar_raw_f = colbar_raw_f.rename(columns={'REF_AREA': 'CountryCode',
                                                'TIME_PERIOD': 'Year',
                                                'OBS_VALUE': 'Value',
                                                'UNIT_MEASURE': 'Unit'})
    colbar_raw_f['IndicatorCode'] = 'UNEMPL'
    colbar_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(colbar_raw_f.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "UNEMPL")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/COLBAR", methods=['GET'])
@login_required
def compute_colbar():
    if not sspi_raw_api_data.raw_data_available("COLBAR"):
        return redirect(url_for("collect_bp.COLBAR"))
    raw_data = sspi_raw_api_data.fetch_raw_data("COLBAR")
    csv_virtual_file = StringIO(raw_data[0]["Raw"]["csv"])
    colbar_raw = pd.read_csv(csv_virtual_file)
    colbar_raw = colbar_raw[['REF_AREA',
                             'TIME_PERIOD', 'UNIT_MEASURE', 'OBS_VALUE']]
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
