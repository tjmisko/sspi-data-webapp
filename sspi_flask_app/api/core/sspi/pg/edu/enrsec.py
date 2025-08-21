from flask import Response, current_app as app
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_forward,
    extrapolate_backward,
    interpolate_linear,
    impute_reference_class_average
)


@compute_bp.route("/ENRSEC", methods=['POST'])
@login_required
def compute_enrsec():
    app.logger.info("Running /api/v1/compute/ENRSEC")
    sspi_indicator_data.delete_many({"IndicatorCode": "ENRSEC"})
    enrsec_clean = sspi_clean_api_data.find({"DatasetCode": "UIS_ENRSEC"})
    lg, ug = sspi_metadata.get_goalposts("ENRSEC")
    scored_list, _ = score_indicator(
        enrsec_clean, "ENRSEC",
        score_function=lambda UIS_ENRSEC: goalpost(UIS_ENRSEC, lg, ug),
        unit="Percent"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/ENRSEC", methods=['POST'])
@login_required
def impute_enrsec():
    app.logger.info("Running /api/v1/impute/ENRSEC")
    sspi_imputed_data.delete_many({"IndicatorCode": "ENRSEC"})
    clean_enrsec = sspi_clean_api_data.find({"DatasetCode": "UIS_ENRSEC"})
    forward = extrapolate_forward(clean_enrsec, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(clean_enrsec, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_enrsec, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    chn_enrsec = impute_reference_class_average("CHN", 2000, 2023, "Dataset", "UIS_ENRSEC", clean_enrsec)
    nga_enrsec = impute_reference_class_average("NGA", 2000, 2023, "Dataset", "UIS_ENRSEC", clean_enrsec)
    imputed_enrsec = forward + backward + interpolated + chn_enrsec + nga_enrsec
    lg, ug = sspi_metadata.get_goalposts("ENRSEC")
    scored_list, _ = score_indicator(
        imputed_enrsec, "ENRSEC",
        score_function=lambda UIS_ENRSEC: goalpost(UIS_ENRSEC, lg, ug),
        unit="Percent"
    )

    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
