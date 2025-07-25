from flask import Response, current_app as app
from flask_login import current_user, login_required
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    zip_intermediates,
)
from sspi_flask_app.api.datasource.unfao import collect_unfao_data
import jq


# @collect_bp.route("/BEEFMK", methods=["GET"])
# @login_required
# def beefmk():
#     def collect_iterator(**kwargs):
#         # yield from collect_unfao_data("2312%2C2313", "1806%2C1746", "QCL", "BEEFMK", **kwargs)
#         # yield from collect_unfao_data("C2510%2C2111%2C2413", "1806%2C1746", "QCL", "BEEFMK", **kwargs)
#         # yield from collect_world_bank_data("SP.POP.TOTL", "BEEFMK", IntermediateCode="POPULN", **kwargs)
#         yield from collectUNFAOData(
#             "2910%2C645%2C2610%2C2510%2C511", "2731%2C2501", "FBS", "BEEFMK", **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/BEEFMK", methods=["GET"])
@login_required
def compute_beefmk():
    app.logger.info("Running /api/v1/compute/BEEFMK")
    sspi_clean_api_data.delete_many({"IndicatorCode": "BEEFMK"})
    prod_lg, prod_ug = 50, 0
    cons_lg, cons_ug = 50, 0

    def score_beefmk(BFPROD, BFCONS, POPULN):
        prod_per_cap = BFPROD / POPULN
        score_prod = goalpost(prod_per_cap, prod_lg, prod_ug)
        score_cons = goalpost(BFCONS, cons_lg, cons_ug)
        return (score_prod + score_cons) / 2

    raw_data = sspi_raw_api_data.fetch_raw_data("BEEFMK", SourceOrganization="UNFAO")
    # return parse_json(jq.compile('.[].Raw.data.[]').input(raw_data).all())
    jq_filter = (
        ".[].Raw.data.[] | select( "
        '.Element == "Production" or '
        '.Element == "Food supply quantity (kg/capita/yr)" or '
        '.Element == "Total Population - Both sexes") | '
        'select(."Area Code (ISO3)" | length == 3) | '
        'select(."Area Code (ISO3)" | test("^[A-Z]{3}$"))'
    )
    all_observations = jq.compile(jq_filter).input(raw_data).all()
    jq_transform = (
        ".[] | {"
        'IndicatorCode: "BEEFMK", '
        'CountryCode: ."Area Code (ISO3)", '
        "Year: (.Year | tonumber), "
        "Value: (.Value | tonumber), "
        "Unit: .Unit, "
        "IntermediateCode: .Element,"
        'UNFAOFlag: ."Flag Description"'
        "}"
    )
    intermediates_list = jq.compile(jq_transform).input(all_observations).all()
    intermediate_map = {
        "Production": "BFPROD",
        "Food supply quantity (kg/capita/yr)": "BFCONS",
        "Total Population - Both sexes": "POPULN",
    }
    for obs in intermediates_list:
        obs["IntermediateCode"] = intermediate_map[obs["IntermediateCode"]]
        if obs["IntermediateCode"] == "BFPROD":
            obs["Value"] = obs["Value"] * 1e6
            obs["Unit"] = "kg"
        elif obs["IntermediateCode"] == "POPULN":
            obs["Value"] = obs["Value"] * 1e3
            obs["Unit"] = "Persons"
    clean_list, incomplete_list = zip_intermediates(
        intermediates_list, "BEEFMK", ScoreFunction=score_beefmk, ScoreBy="Value"
    )
    sspi_incomplete_api_data.insert_many(incomplete_list)
    sspi_clean_api_data.insert_many(clean_list)
    return parse_json(clean_list)
