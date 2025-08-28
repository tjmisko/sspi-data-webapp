from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_reference_class_average,
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)


@compute_bp.route("/TAXREV", methods=["POST"])
@login_required
def compute_taxrev():
    app.logger.info("Running /api/v1/compute/TAXREV")
    sspi_indicator_data.delete_many({"IndicatorCode": "TAXREV"})
    # Fetch clean dataset
    taxrev_clean = sspi_clean_api_data.find({"DatasetCode": "WB_TAXREV"})
    lg, ug = sspi_metadata.get_goalposts("TAXREV")
    scored_list, _ = score_indicator(
        taxrev_clean, "TAXREV",
        score_function = lambda WB_TAXREV: goalpost(WB_TAXREV, lg, ug),
        unit="Percentage"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/TAXREV", methods=['POST'])
@login_required
def impute_taxrev():
    app.logger.info("Running /api/v1/impute/TAXREV")
    sspi_imputed_data.delete_many({"IndicatorCode": "TAXREV"})
    clean_taxrev = sspi_clean_api_data.find({"DatasetCode": "WB_TAXREV"})
    forward = extrapolate_forward(clean_taxrev, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(clean_taxrev, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_taxrev, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    imputed_taxrev = forward + backward + interpolated
    # Handle VNM, NGA, VEN, DZA : each is missing all observations
    vnm_taxrev = impute_reference_class_average("VNM", 2000, 2023, "Dataset", "WB_TAXREV", clean_taxrev)
    nga_taxrev = impute_reference_class_average("NGA", 2000, 2023, "Dataset", "WB_TAXREV", clean_taxrev)
    ven_taxrev = impute_reference_class_average("VEN", 2000, 2023, "Dataset", "WB_TAXREV", clean_taxrev)
    dza_taxrev = impute_reference_class_average("DZA", 2000, 2023, "Dataset", "WB_TAXREV", clean_taxrev)
    lg, ug = sspi_metadata.get_goalposts("TAXREV")
    scored_list, _ = score_indicator(
        imputed_taxrev + vnm_taxrev + nga_taxrev + ven_taxrev + dza_taxrev, 
        "TAXREV",
        score_function = lambda WB_TAXREV: goalpost(WB_TAXREV, lg, ug),
        unit="Percentage"
    )
    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
