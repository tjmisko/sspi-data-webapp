from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_reference_class_average
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata,
    sspi_imputed_data
)

@compute_bp.route("/PRISON", methods=["POST"])
@login_required
def compute_prison():
    app.logger.info("Running /api/v1/compute/PRISON")
    sspi_indicator_data.delete_many({"IndicatorCode": "PRISON"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "PRISON"})
    unodc_pripop = sspi_clean_api_data.find({"DatasetCode": "UNODC_PRIPOP"})
    lg, ug = sspi_metadata.get_goalposts("PRISON")
    clean_list, _ = score_indicator(
        unodc_pripop,
        "PRISON",
        score_function=lambda UNODC_PRIPOP: goalpost(UNODC_PRIPOP, lg, ug),
        unit="Prisoners per 100,000 population",
    )
    sspi_indicator_data.insert_many(clean_list)
    return parse_json(clean_list)

@impute_bp.route("/PRISON", methods=["POST"])
@login_required
def impute_prison():
    app.logger.info("Running /api/v1/impute/PRISON")
    sspi_imputed_data.delete_many({"IndicatorCode": "PRISON"})
    unodc_pripop = sspi_clean_api_data.find({"DatasetCode": "UNODC_PRIPOP"})
    forward = extrapolate_forward(unodc_pripop, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(unodc_pripop, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(unodc_pripop, ["CountryCode", "DatasetCode"], impute_only=True)
    prison_chn = impute_reference_class_average(
        "CHN", 2000, 2023, "Dataset", "UNODC_PRIPOP", unodc_pripop
    )
    lg, ug = sspi_metadata.get_goalposts("PRISON")
    imputed_list, _ = score_indicator(
        forward + backward + interpolated + prison_chn,
        "PRISON",
        score_function=lambda UNODC_PRIPOP: goalpost(UNODC_PRIPOP, lg, ug),
        unit="Prisoners per 100,000 population",
    )
    sspi_imputed_data.insert_many(imputed_list)
    return parse_json(imputed_list)
