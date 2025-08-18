from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    slice_dataset,
    score_indicator,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_global_average
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_incomplete_indicator_data,
    sspi_metadata
)


# @collect_bp.route("/FDEPTH", methods=['POST'])
# @login_required
# def fdepth():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("FS.AST.PRVT.GD.ZS", "FDEPTH", IntermediateCode="CREDIT", **kwargs)
#         yield from collect_wb_data("GFDD.OI.02", "FDEPTH", IntermediateCode="DPOSIT", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/FDEPTH", methods=['POST'])
@login_required
def compute_fdepth():
    app.logger.info("Running /api/v1/compute/FDEPTH")
    sspi_indicator_data.delete_many({"IndicatorCode": "FDEPTH"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "FDEPTH"})
    # Fetch clean datasets
    credit_clean = sspi_clean_api_data.find({"DatasetCode": "WB_CREDIT"})
    deposit_clean = sspi_clean_api_data.find({"DatasetCode": "WB_DPOSIT"})
    combined_list = credit_clean + deposit_clean
    clean_list, incomplete_list = score_indicator(
        combined_list, "FDEPTH",
        score_function=lambda CREDIT, DPOSIT: (CREDIT + DPOSIT) / 2,
        unit="Index"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/FDEPTH", methods=['POST'])
@login_required
def impute_fdepth():
    """
    Steps to Impute
    1. Assemble separate series
    2. Run usual imputations
    3. Filter out only those observations which contain at least one imputation

    It must be done in this admittedly inefficient way to avoid imputing over 
    valid data.
    """
    app.logger.info("Running /api/v1/impute/FDEPTH")
    sspi_67 = sspi_metadata.country_group("SSPI67")
    sspi_imputed_data.delete_many({"IndicatorCode": "FDEPTH"})
    clean_fdepth = sspi_clean_api_data.find({"IndicatorCode": "FDEPTH", "CountryCode": {"$in": sspi_67}, "Year": {"$gte": 2000}})
    clean_credit = slice_dataset(clean_fdepth, "CREDIT")
    clean_dposit = slice_dataset(clean_fdepth, "DPOSIT")
    incomplete_fdepth = sspi_incomplete_indicator_data.find({"IndicatorCode": "FDEPTH", "CountryCode": {"$in": sspi_67}})
    incomplete_credit = slice_dataset(incomplete_fdepth, "CREDIT")
    incomplete_dposit = slice_dataset(incomplete_fdepth, "DPOSIT")
    obs_credit = clean_credit + incomplete_credit
    obs_dposit = clean_dposit + incomplete_dposit
    forward_credit = extrapolate_forward(obs_credit, 2023, impute_only=True)
    # return parse_json(obs_credit)
    backward_credit = extrapolate_backward(obs_credit, 2000, impute_only=True)
    interpolated_credit = interpolate_linear(obs_credit, impute_only=True)
    # return parse_json(obs_credit)
    all_credit = obs_credit + forward_credit + backward_credit + interpolated_credit
    forward_dposit = extrapolate_forward(obs_dposit, 2023, impute_only=True)
    backward_dposit = extrapolate_backward(obs_dposit, 2000, impute_only=True)
    interpolated_dposit = interpolate_linear(obs_dposit, impute_only=True)
    gbr_dposit = impute_global_average("GBR", 2000, 2023, "Intermediate", "DPOSIT", clean_dposit)
    all_dposit = obs_dposit + forward_dposit + backward_dposit + interpolated_dposit + gbr_dposit
    clean_list, incomplete_list = score_indicator(
        all_credit + all_dposit, "FDEPTH",
        score_function=lambda CREDIT, DPOSIT: (CREDIT + DPOSIT) / 2,
        unit="Index"
    )
    imputed_fdepth = []
    for obs in clean_list:
        if any([inter.get("Imputed", False) for inter in obs["Intermediates"]]):
           imputed_fdepth.append(obs) 
    sspi_imputed_data.insert_many(imputed_fdepth) 
    return parse_json(imputed_fdepth)
