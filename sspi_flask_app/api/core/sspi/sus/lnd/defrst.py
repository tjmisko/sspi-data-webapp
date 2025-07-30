from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.unfao import collect_unfao_data, format_fao_data_series
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    goalpost
)


# @collect_bp.route("/DEFRST", methods=['GET'])
# @login_required
# def defrst():
#     def collect_iterator(**kwargs):
#         yield from collect_unfao_data("5110", "6717", "RL", "DEFRST", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/DEFRST", methods=['GET'])
@login_required
def compute_defrst():
    app.logger.info("Running /api/v1/compute/DEFRST")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DEFRST"})
    lg, ug = sspi_metadata.get_goalposts("DEFRST")
    raw_data = sspi_raw_api_data.fetch_raw_data("DEFRST")[0]["Raw"]["data"]
    clean_obs_list = format_fao_data_series(raw_data, "DEFRST")
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


