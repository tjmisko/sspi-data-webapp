from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.ilo import collectILOData
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
import json
import pandas as pd
from io import StringIO


# @collect_bp.route("/EMPLOY")
# @login_required
# def lfpart():
#     def collect_iterator(**kwargs):
#         yield from collectILOData(
#             "DF_EAP_DWAP_SEX_AGE_RT",
#             "EMPLOY",
#             QueryParams=".A...AGE_AGGREGATE_Y25-54",
#             **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username),
#         mimetype='text/event-stream'
#     )


@compute_bp.route("/EMPLOY", methods=['GET'])
@login_required
def compute_employ():
    app.logger.info("Running /api/v1/compute/EMPLOY")
    sspi_clean_api_data.delete_many({"IndicatorCode": "EMPLOY"})
    raw_data = sspi_raw_api_data.fetch_raw_data("EMPLOY")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    employ_raw = pd.read_csv(csv_virtual_file)
    employ_raw_f = employ_raw[['REF_AREA', 'TIME_PERIOD', 'MEASURE', 'SEX',
                               'UNIT_MEASURE', 'OBS_VALUE']]
    colmap_rename = {
        'REF_AREA': 'CountryCode',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value',
        'UNIT_MEASURE': 'Unit'
    }
    employ_raw_f = employ_raw_f[employ_raw_f['SEX'] == 'SEX_T']
    employ_raw_f = employ_raw_f.rename(columns=colmap_rename,errors="ignore")
    employ_raw_f['IndicatorCode'] = 'EMPLOY'
    employ_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(str(employ_raw_f.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "EMPLOY")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
