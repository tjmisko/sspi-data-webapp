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
import pandas as pd
from io import StringIO
import json


# @collect_bp.route("/FATINJ")
# @login_required
# def fatinj():
#     def collect_iterator(**kwargs):
#         yield from collectILOData("DF_SDG_F881_SEX_MIG_RT", "FATINJ", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/FATINJ", methods=["GET"])
@login_required
def compute_fatinj():
    app.logger.info("Running /api/v1/compute/FATINJ")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FATINJ"})
    raw_data = sspi_raw_api_data.fetch_raw_data("FATINJ")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    fatinj_raw = pd.read_csv(csv_virtual_file)
    fatinj_raw = fatinj_raw[fatinj_raw["SEX"] == "SEX_T"]
    fatinj_raw = fatinj_raw[["REF_AREA", "TIME_PERIOD", "UNIT_MEASURE", "OBS_VALUE"]]
    fatinj_raw = fatinj_raw.rename(
        columns={
            "REF_AREA": "CountryCode",
            "TIME_PERIOD": "Year",
            "OBS_VALUE": "Value",
            "UNIT_MEASURE": "Unit",
        }
    )
    fatinj_raw["IndicatorCode"] = "FATINJ"
    fatinj_raw["Unit"] = "Rate per 100,000"
    fatinj_raw.dropna(subset=["Value"], inplace=True)
    obs_list = json.loads(str(fatinj_raw.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "FATINJ")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
