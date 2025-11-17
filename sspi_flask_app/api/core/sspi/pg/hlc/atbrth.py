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
    extrapolate_forward,
    extrapolate_backward,
    interpolate_linear,
    impute_reference_class_average)

from sspi_flask_app.auth.decorators import admin_required


@compute_bp.route("/ATBRTH", methods=["POST"])
@admin_required
def compute_atbrth():
    app.logger.info("Running /api/v1/compute/ATBRTH")
    sspi_indicator_data.delete_many({"IndicatorCode": "ATBRTH"})
    atbrth_clean = sspi_clean_api_data.find({"DatasetCode": "WHO_ATBRTH"})
    lg, ug = sspi_metadata.get_goalposts("ATBRTH")
    scored_list, _ = score_indicator(
        atbrth_clean, "ATBRTH",
        score_function=lambda WHO_ATBRTH: goalpost(WHO_ATBRTH, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/ATBRTH", methods=["POST"])
@admin_required
def impute_atbrth():
    sspi_imputed_data.delete_many({"IndicatorCode": "ATBRTH"})
    atbrth_clean = sspi_clean_api_data.find({"DatasetCode": "WHO_ATBRTH"})
    forward = extrapolate_forward(atbrth_clean, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(atbrth_clean, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    atbrth_che = impute_reference_class_average("CHE", 2000, 2023, "Dataset", "WHO_ATBRTH", atbrth_clean)
    atbrth_gbr = impute_reference_class_average("GBR", 2000, 2023, "Dataset", "WHO_ATBRTH", atbrth_clean)
    atbrth_nld = impute_reference_class_average("NLD", 2000, 2023, "Dataset", "WHO_ATBRTH", atbrth_clean)
    atbrth_bel = impute_reference_class_average("BEL", 2000, 2023, "Dataset", "WHO_ATBRTH", atbrth_clean)
    atbrth_swe = impute_reference_class_average("SWE", 2000, 2023, "Dataset", "WHO_ATBRTH", atbrth_clean)
    interpolated = interpolate_linear(atbrth_clean, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("ATBRTH")
    scored_list, _ = score_indicator(
        forward + backward + interpolated + atbrth_che + atbrth_gbr + atbrth_nld + atbrth_bel + atbrth_swe, 
        "ATBRTH",
        score_function=lambda WHO_ATBRTH: goalpost(WHO_ATBRTH, lg, ug),
        unit="%"
    )
    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
