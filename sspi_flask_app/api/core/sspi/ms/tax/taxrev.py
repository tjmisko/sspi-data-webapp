from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.datasource.worldbank import clean_wb_data, collect_world_bank_data
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_global_average,
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_raw_api_data,
    sspi_metadata
)


# @collect_bp.route("/TAXREV", methods=['GET'])
# @login_required
# def taxrev():
#     def collect_iterator(**kwargs):
#         yield from collect_world_bank_data("GC.TAX.TOTL.GD.ZS", "TAXREV", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/TAXREV")
@login_required
def compute_taxrev():
    app.logger.info("Running /api/v1/compute/TAXREV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "TAXREV"})
    taxrev_raw = sspi_raw_api_data.fetch_raw_data("TAXREV")
    taxrev_clean = clean_wb_data(taxrev_raw, "TAXREV", "% of GDP")
    lg, ug = sspi_metadata.get_goalposts("TAXREV")
    scored_list, _ = score_indicator(
        taxrev_clean, "TAXREV",
        score_function = lambda WB_TAXREV: goalpost(WB_TAXREV, lg, ug),
        unit="Percentage"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/TAXREV", methods=['POST'])
@login_required
def impute_taxrev():
    app.logger.info("Running /api/v1/impute/TAXREV")
    sspi_imputed_data.delete_many({"IndicatorCode": "TAXREV"})
    clean_taxrev = sspi_clean_api_data.find({"IndicatorCode": "TAXREV"})
    forward = extrapolate_forward(clean_taxrev, 2023, impute_only=True)
    backward = extrapolate_backward(clean_taxrev, 2000, impute_only=True)
    interpolated = interpolate_linear(clean_taxrev, impute_only=True)
    imputed_taxrev = forward + backward + interpolated
    # Handle VNM, NGA, VEN, DZA : each is missing all observations
    vnm_taxrev = impute_global_average("VNM", 2000, 2023, "Indicator", "TAXREV", clean_taxrev)
    nga_taxrev = impute_global_average("NGA", 2000, 2023, "Indicator", "TAXREV", clean_taxrev)
    ven_taxrev = impute_global_average("VEN", 2000, 2023, "Indicator", "TAXREV", clean_taxrev)
    dza_taxrev = impute_global_average("DZA", 2000, 2023, "Indicator", "TAXREV", clean_taxrev)
    sspi_imputed_data.insert_many(imputed_taxrev + vnm_taxrev + nga_taxrev + ven_taxrev + dza_taxrev)
    return parse_json(imputed_taxrev + vnm_taxrev + nga_taxrev + ven_taxrev + dza_taxrev)
