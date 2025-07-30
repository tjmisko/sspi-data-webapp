from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.datasource.prisonstudies import (
    collect_prison_studies_data,
    scrape_stored_pages_for_data,
)
from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data,
    collect_world_bank_data,
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_incomplete_indicator_data,
    sspi_metadata,
    sspi_raw_api_data,
)

# @collect_bp.route("/PRISON", methods=["GET"])
# @login_required
# def prison():
#     def collect_iterator(**kwargs):
#         yield from collect_world_bank_data(
#             "SP.POP.TOTL", "PRISON", IntermediateCode="POPULN", **kwargs
#         )
#         yield from collect_prison_studies_data(IntermediateCode="PRIPOP", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/PRISON", methods=["GET"])
@login_required
def compute_prison():
    app.logger.info("Running /api/v1/compute/PRISON")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PRISON"})
    details = sspi_metadata.find(
        {"DocumentType": "IndicatorDetail", "Metadata.IndicatorCode": "PRISON"}
    )[0]
    lg = details["Metadata"]["LowerGoalpost"]
    ug = details["Metadata"]["UpperGoalpost"]
    pop_data = sspi_raw_api_data.fetch_raw_data("PRISON", IntermediateCode="POPULN")
    cleaned_pop = clean_wb_data(pop_data, "PRISON", "Population")
    clean_data_list, missing_data_list = scrape_stored_pages_for_data()
    combined_list = cleaned_pop + clean_data_list
    clean_list, incomplete_list = score_indicator(
        combined_list,
        "PRISON",
        score_function=lambda PRIPOP, POPULN: goalpost(PRIPOP / POPULN * 100000, lg, ug),
        unit=lambda PRIPOP, POPULN: "Prisoners Per 100,000"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
