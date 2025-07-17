from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    goalpost,
)
from sspi_flask_app.api.datasource.prisonstudies import (
    collectPrisonStudiesData,
    scrape_stored_pages_for_data,
)
from sspi_flask_app.api.datasource.worldbank import collectWorldBankdata, clean_wb_data


# @collect_bp.route("/PRISON", methods=["GET"])
# @login_required
# def prison():
#     def collect_iterator(**kwargs):
#         yield from collectWorldBankdata(
#             "SP.POP.TOTL", "PRISON", IntermediateCode="POPULN", **kwargs
#         )
#         yield from collectPrisonStudiesData(IntermediateCode="PRIPOP", **kwargs)
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
    clean_list, incomplete_list = zip_intermediates(
        combined_list,
        "PRISON",
        ScoreFunction=lambda PRIPOP, POPULN: goalpost(PRIPOP / POPULN * 100000, lg, ug),
        ValueFunction=lambda PRIPOP, POPULN: PRIPOP / POPULN * 100000,
        UnitFunction=lambda PRIPOP, POPULN: "Prisoners Per 100,000",
        ScoreBy="Value",
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
