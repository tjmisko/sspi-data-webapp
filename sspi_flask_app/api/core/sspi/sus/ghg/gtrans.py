from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.api.datasource.iea import collect_iea_data
from sspi_flask_app.api.datasource.worldbank import collect_world_bank_data
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
from sspi_flask_app.api.datasource.worldbank import clean_wb_data
from sspi_flask_app.api.datasource.iea import clean_IEA_data_GTRANS


# @collect_bp.route("/GTRANS", methods=["GET"])
# @login_required
# def gtrans():
#     def collect_iterator(**kwargs):
#         yield from collect_iea_data(
#             "CO2BySector",
#             "GTRANS",
#             IntermediateCode="TCO2EQ",
#             SourceOrganization="IEA",
#             **kwargs,
#         )
#         yield from collect_world_bank_data(
#             "SP.POP.TOTL", "GTRANS", IntermediateCode="POPULN", **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/GTRANS", methods=["GET"])
@login_required
def compute_gtrans():
    app.logger.info("Running /api/v1/compute/GTRANS")
    sspi_clean_api_data.delete_many({"IndicatorCode": "GTRANS"})
    lg = 7500
    ug = 0
    pop_data = sspi_raw_api_data.fetch_raw_data("GTRANS", IntermediateCode="POPULN")
    cleaned_pop = clean_wb_data(pop_data, "GTRANS", "Population")
    gtrans = sspi_raw_api_data.fetch_raw_data("GTRANS", IntermediateCode="TCO2EQ")
    cleaned_co2 = clean_IEA_data_GTRANS(gtrans, "GTRANS", "CO2 from transport sources")
    document_list = cleaned_pop + cleaned_co2
    clean_list, incomplete_list = zip_intermediates(
        document_list,
        "GTRANS",
        ScoreFunction=lambda TCO2EQ, POPULN: goalpost(TCO2EQ / POPULN, lg, ug),
        ValueFunction=lambda TCO2EQ, POPULN: TCO2EQ / POPULN,
        ScoreBy="Value",
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
