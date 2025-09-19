from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_reference_class_average
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)


@compute_bp.route("/ARMEXP", methods=['POST'])
@login_required
def compute_armexp():
    app.logger.info("Running /api/v1/compute/ARMEXP")
    sspi_indicator_data.delete_many({"IndicatorCode": "ARMEXP"})
    clean_armexp = sspi_clean_api_data.find({"DatasetCode": "SIPRI_ARMEXP"})
    lg, ug = sspi_metadata.get_goalposts("ARMEXP")
    scored_list, _ = score_indicator(
        clean_armexp, "ARMEXP",
        score_function=lambda SIPRI_ARMEXP: goalpost(SIPRI_ARMEXP, lg, ug),
        unit="Expenditure"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/ARMEXP", methods=['POST'])
@login_required
def impute_armexp():
    app.logger.info("Running /api/v1/impute/ARMEXP")
    sspi_imputed_data.delete_many({"IndicatorCode": "ARMEXP"})
    clean_armexp = sspi_clean_api_data.find({"DatasetCode": "SIPRI_ARMEXP"})
    forward = extrapolate_forward(clean_armexp, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(clean_armexp, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_armexp, ["CountryCode", "DatasetCode"], impute_only=True)
    impute_are = impute_reference_class_average(
        "ARE", 2000, 2023, "Dataset", "SIPRI_ARMEXP", clean_armexp
    )
    impute_bgd = impute_reference_class_average(
        "BGD", 2000, 2023, "Dataset", "SIPRI_ARMEXP", clean_armexp
    )
    impute_irq = impute_reference_class_average(
        "IRQ", 2000, 2023, "Dataset", "SIPRI_ARMEXP", clean_armexp
    )
    lg, ug = sspi_metadata.get_goalposts("ARMEXP")
    scored_list, _ = score_indicator(
        forward + backward + interpolated + impute_are + impute_bgd + impute_irq, "ARMEXP",
        score_function=lambda SIPRI_ARMEXP: goalpost(SIPRI_ARMEXP, lg, ug),
        unit="Expenditure"
    )
    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
