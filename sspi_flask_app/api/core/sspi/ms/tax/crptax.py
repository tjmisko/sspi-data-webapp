from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.taxfoundation import collectTaxFoundationData, cleanTaxFoundation
from sspi_flask_app.api.resources.utilities import parse_json, score_single_indicator
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)


@collect_bp.route("/CRPTAX", methods=['GET'])
@login_required
def crptax():
    def collect_iterator(**kwargs):
        yield from collectTaxFoundationData('CRPTAX', **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/CRPTAX")
@login_required
def compute_crptax():
    app.logger.info("Running /api/v1/compute/CRPTAX")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CRPTAX"})
    crptax_raw = sspi_raw_api_data.fetch_raw_data("CRPTAX")
    crptax_clean = cleanTaxFoundation(crptax_raw, "CRPTAX", "Tax Rate", "Corporate Taxes")
    scored_list = score_single_indicator(crptax_clean, "CRPTAX")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
