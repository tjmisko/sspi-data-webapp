from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)
from sspi_flask_app.api.datasource.worldbank import clean_wb_data
from sspi_flask_app.api.datasource.taxfoundation import cleanTaxFoundation


@compute_bp.route("/TAXREV")
@login_required
def compute_taxrev():
    if not sspi_raw_api_data.raw_data_available("TAXREV"):
        return redirect(url_for("api_bp.collect_bp.TAXREV"))
    taxrev_raw = sspi_raw_api_data.fetch_raw_data("TAXREV")
    taxrev_clean = clean_wb_data(taxrev_raw, "TAXREV", "% of GDP")
    scored = score_single_indicator(taxrev_clean, "TAXREV")
    filtered_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)


@compute_bp.route("/CRPTAX")
@login_required
def compute_crptax():
    if not sspi_raw_api_data.raw_data_available("CRPTAX"):
        return redirect(url_for("api_bp.collect_bp.CRPTAX"))
    crptax_raw = sspi_raw_api_data.fetch_raw_data("CRPTAX")
    crptax_clean = cleanTaxFoundation(crptax_raw, "CRPTAX", "Tax Rate", "Corporate Taxes")
    scored = score_single_indicator(crptax_clean, "CRPTAX")
    filtered_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(scored)
