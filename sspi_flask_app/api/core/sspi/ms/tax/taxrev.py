from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.worldbank import (
    collectWorldBankdata,
    clean_wb_data
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)


@collect_bp.route("/TAXREV", methods=['GET'])
@login_required
def taxrev():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("GC.TAX.TOTL.GD.ZS", "TAXREV", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/TAXREV")
@login_required
def compute_taxrev():
    app.logger.info("Running /api/v1/compute/TAXREV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "TAXREV"})
    taxrev_raw = sspi_raw_api_data.fetch_raw_data("TAXREV")
    taxrev_clean = clean_wb_data(taxrev_raw, "TAXREV", "% of GDP")
    scored_list = score_single_indicator(taxrev_clean, "TAXREV")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
