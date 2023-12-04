from flask import flash, redirect, url_for
from flask_login import login_required
from ..api import api_bp
from ... import sspi_clean_api_data, sspi_imputed_data, sspi_dynamic_data
from sspi_flask_app.api.resources.utilities import parse_json

@api_bp.route("/finalize/<indicator_code>")
@login_required
def finalize(indicator_code):
    api_data = parse_json(sspi_clean_api_data.find({"IndicatorCode": indicator_code}, {"_id": 0}))
    imputed_data = parse_json(sspi_imputed_data.find({"IndicatorCode": indicator_code}, {"_id": 0}))
    print(api_data)
    print(imputed_data)
    final_data = api_data + imputed_data
    print(type(final_data))
    count = len(final_data)
    sspi_dynamic_data.insert_many(final_data)
    flash(f"Inserted {count} documents into SSPI Dynamic Data Database for {indicator_code}")
    return redirect(url_for("api_bp.api_dashboard"))