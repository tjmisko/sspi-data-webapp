import json
from io import StringIO

import pandas as pd
from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.datasource.ilo import collect_ilo_data
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import sspi_clean_api_data, sspi_raw_api_data, sspi_metadata

# @collect_bp.route("/COLBAR")
# @login_required
# def colbar():
#     def collect_iterator(**kwargs):
#         url_params = ["startPeriod=1990-01-01", "endPeriod=2024-12-31"]
#         yield from collect_ilo_data(
#             "DF_ILR_CBCT_NOC_RT", "COLBAR", URLParams=url_params, **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


# @compute_bp.route("/COLBAR", methods=["GET"])
# @login_required
# def compute_colbar():
    # app.logger.info("Running /api/v1/compute/COLBAR")
    # sspi_clean_api_data.delete_many({"IndicatorCode": "COLBAR"})
    # raw_data = sspi_raw_api_data.fetch_raw_data("COLBAR")
    # csv_virtual_file = StringIO(raw_data[0]["Raw"])
    # colbar_raw = pd.read_csv(csv_virtual_file)
    # colbar_raw = colbar_raw[["REF_AREA", "TIME_PERIOD", "UNIT_MEASURE", "OBS_VALUE"]]
    # colbar_raw = colbar_raw.rename(
    #     columns={
    #         "REF_AREA": "CountryCode",
    #         "TIME_PERIOD": "Year",
    #         "OBS_VALUE": "Value",
    #         "UNIT_MEASURE": "Unit",
    #     }
    # )
    # colbar_raw["IndicatorCode"] = "COLBAR"
    # colbar_raw["Unit"] = "Proportion"
    # colbar_raw["Value"] = colbar_raw["Value"]
    # obs_list = json.loads(str(colbar_raw.to_json(orient="records")))
    # lg, ug = sspi_metadata.get_goalposts("COLBAR")
    # scored_list, _ = score_indicator(
    #    obs_list, "COLBAR",
    #    score_function=lambda ILO_COLBAR: goalpost(ILO_COLBAR, lg, ug),
    #    unit = "%"
    # )
    # sspi_clean_api_data.insert_many(scored_list)
    # return parse_json(scored_list)
