from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata,
    sspi_imputed_data
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_forward)

from sspi_flask_app.auth.decorators import admin_required


# @collect_bp.route("/EDEMOC", methods=['POST'])
# @admin_required
# def edemoc():
#     def collect_iterator(**kwargs):
#         yield from collectVDEMData("v2x_polyarchy", "EDEMOC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/EDEMOC", methods=['POST'])
@admin_required
def compute_edemoc():
    app.logger.info("Running /api/v1/compute/EDEMOC")
    sspi_indicator_data.delete_many({"IndicatorCode": "EDEMOC"})
    edemoc_clean = sspi_clean_api_data.find({"DatasetCode": "VDEM_EDEMOC"})
    lg, ug = sspi_metadata.get_goalposts("EDEMOC")
    scored_list, _ = score_indicator(
        edemoc_clean, "EDEMOC",
        score_function=lambda VDEM_EDEMOC: goalpost(VDEM_EDEMOC, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/EDEMOC", methods=['POST'])
def impute_edemoc():
    sspi_imputed_data.delete_many({"IndicatorCode": "EDEMOC"})
    edemoc_clean = sspi_clean_api_data.find({"DatasetCode": "VDEM_EDEMOC"})
    edemoc_clean = extrapolate_forward(
        edemoc_clean, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True
    )
    lg, ug = sspi_metadata.get_goalposts("EDEMOC")
    scored_list, _ = score_indicator(
        edemoc_clean, "EDEMOC",
        score_function=lambda VDEM_EDEMOC: goalpost(VDEM_EDEMOC, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
