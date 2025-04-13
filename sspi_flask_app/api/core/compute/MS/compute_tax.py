from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.worldbank import clean_wb_data
from sspi_flask_app.api.datasource.taxfoundation import cleanTaxFoundation


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
