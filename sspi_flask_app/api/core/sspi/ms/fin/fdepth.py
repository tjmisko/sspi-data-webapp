from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.core.sspi import impute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.worldbank import (
    collectWorldBankdata,
    clean_wb_data
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
)



@collect_bp.route("/FDEPTH", methods=['GET'])
@login_required
def fdepth():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("FS.AST.PRVT.GD.ZS", "FDEPTH", IntermediateCode="CREDIT", **kwargs)
        yield from collectWorldBankdata("GFDD.OI.02", "FDEPTH", IntermediateCode="DPOSIT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/FDEPTH", methods=['GET'])
@login_required
def compute_fdepth():
    app.logger.info("Running /api/v1/compute/FDEPTH")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FDEPTH"})
    credit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="CREDIT")
    credit_clean = clean_wb_data(credit_raw, "FDEPTH", unit="Percent")
    deposit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="DPOSIT")
    deposit_clean = clean_wb_data(deposit_raw, "FDEPTH", unit="Percent")
    combined_list = credit_clean + deposit_clean
    clean_list, incomplete_list = zip_intermediates(
        combined_list, "FDEPTH",
        ScoreFunction=lambda CREDIT, DPOSIT: (CREDIT + DPOSIT) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/FDEPTH", methods=['POST'])
@login_required
def impute_fdepth():
    app.logger.info("Running /api/v1/impute/FDEPTH")
    sspi_imputed_data.delete_many({"IndicatorCode": "FDEPTH"})
    clean_fdepth = sspi_clean_api_data.find({"IndicatorCode": "FDEPTH"})
    incomplete_fdepth = sspi_incomplete_api_data.find({"IndicatorCode": "FDEPTH"})
    # forward = extrapolate_forward(clean_fdepth, 2023, impute_only=True)
    # backward = extrapolate_backward(clean_fdepth, 2000, impute_only=True)
    # interpolated = interpolate_linear(clean_fdepth, impute_only=True)
    # imputed_fdepth = forward + backward + interpolated
    # sspi_imputed_data.insert_many(imputed_fdepth) 
    return parse_json(incomplete_fdepth)
