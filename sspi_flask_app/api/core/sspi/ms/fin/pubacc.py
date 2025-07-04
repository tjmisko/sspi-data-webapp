from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.worldbank import (
    collectWorldBankdata,
    clean_wb_data
)


@collect_bp.route("/PUBACC", methods=['GET'])
@login_required
def pubacc():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("FX.OWN.TOTL.ZS", "PUBACC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/PUBACC", methods=['GET'])
@login_required
def compute_pubacc():
    app.logger.info("Running /api/v1/compute/PUBACC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PUBACC"})
    pubacc_raw = sspi_raw_api_data.fetch_raw_data("PUBACC")
    pubacc_clean = clean_wb_data(pubacc_raw, "PUBACC", unit="Percent")
    pubacc_clean = score_single_indicator(pubacc_clean, "PUBACC")
    sspi_clean_api_data.insert_many(pubacc_clean)
    return parse_json(pubacc_clean)
