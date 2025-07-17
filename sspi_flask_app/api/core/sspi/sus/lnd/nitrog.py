from sspi_flask_app.api.core.sspi import collect_bp
from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.api.datasource.epi import collectEPIData
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator,
)
import pandas as pd
import re
from io import StringIO
import json


# @collect_bp.route("/NITROG", methods=['GET'])
# @login_required
# def nitrog():
#     def collect_iterator(**kwargs):
#         yield from collectEPIData("SNM_ind_na.csv", "NITROG", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


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
    SNM_long.drop(SNM_long[SNM_long['Value'] < 0].index.tolist(), inplace=True)
    SNM_long.drop(SNM_long[SNM_long['Value'].isna()].index.tolist(), inplace=True)
    SNM_long['IndicatorCode'] = 'NITROG'
    SNM_long['Unit'] = 'Index'
    obs_list = json.loads(str(SNM_long.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "NITROG")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


