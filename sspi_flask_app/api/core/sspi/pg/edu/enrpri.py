from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    extrapolate_forward,
    impute_reference_class_average,
    interpolate_linear,
    parse_json,
    score_indicator,
    goalpost)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata,
)


@compute_bp.route("/ENRPRI", methods=['POST'])
@admin_required
def compute_enrpri():
    app.logger.info("Running /api/v1/compute/ENRPRI")
    sspi_indicator_data.delete_many({"IndicatorCode": "ENRPRI"})
    enrpri_clean = sspi_clean_api_data.find({"DatasetCode": "UIS_ENRPRI"})
    lg, ug = sspi_metadata.get_goalposts("ENRPRI")
    scored_list, _ = score_indicator(
        enrpri_clean, "ENRPRI",
        score_function=lambda UIS_ENRPRI: goalpost(UIS_ENRPRI, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/ENRPRI", methods=['POST'])
@admin_required
def impute_enrpri():
    app.logger.info("Running /api/v1/impute/ENRPRI")
    sspi_imputed_data.delete_many({"IndicatorCode": "ENRPRI"})
    clean_enrpri = sspi_clean_api_data.find({"DatasetCode": "UIS_ENRPRI"})
    forward = extrapolate_forward(clean_enrpri, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(clean_enrpri, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_enrpri, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    imputed_enrpri = forward + backward + interpolated
    # chn_enrpri = impute_reference_class_average("CHN", 2000, 2023, "Dataset", "UIS_ENRPRI", clean_enrpri)
    lg, ug = sspi_metadata.get_goalposts("ENRPRI")
    scored_list, _ = score_indicator(
        imputed_enrpri, "ENRPRI",
        score_function=lambda UIS_ENRPRI: goalpost(UIS_ENRPRI, lg, ug),
        unit="%"
    )

    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
