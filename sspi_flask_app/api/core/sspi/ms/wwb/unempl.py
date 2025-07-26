from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.ilo  import collect_ilo_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from io import StringIO
import pandas as pd
import json


# @collect_bp.route("/UNEMPL")
# @login_required
# def unempl():
#     def collect_iterator(**kwargs):
#         yield from collect_ilo_data("DF_SDG_0131_SEX_SOC_RT", "UNEMPL", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/UNEMPL", methods=['GET'])
@login_required
def compute_unempl():
    app.logger.info("Running /api/v1/compute/UNEMPL")
    sspi_clean_api_data.delete_many({"IndicatorCode": "UNEMPL"})
    raw_data = sspi_raw_api_data.fetch_raw_data("UNEMPL")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    unempl_raw = pd.read_csv(csv_virtual_file)
    unempl_raw_f = unempl_raw[unempl_raw['SOC'] == 'SOC_CONTIG_UNE']
    unempl_raw_f = unempl_raw_f[['REF_AREA',
                                 'TIME_PERIOD', 'UNIT_MEASURE', 'OBS_VALUE']]
    colmap_rename = {
        'REF_AREA': 'CountryCode',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value',
        'UNIT_MEASURE': 'Unit'
    }
    unempl_raw_f = unempl_raw_f.rename(columns=colmap_rename)
    unempl_raw_f['IndicatorCode'] = 'UNEMPL'
    unempl_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(str(unempl_raw_f.to_json(orient="records")))
    lg, ug = sspi_metadata.get_goalposts("UNEMPL")
    scored_list, _ = score_indicator(
        obs_list, "UNEMPL",
        score_function=lambda ILO_UNEMPL: goalpost(ILO_UNEMPL, lg, ug),
        unit="Rate"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
