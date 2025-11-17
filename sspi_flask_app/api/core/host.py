from flask import Blueprint, send_file, current_app as app
from flask_login import login_required
import os

host_bp = Blueprint(
    "host_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/bulk"
)
from sspi_flask_app.auth.decorators import admin_required


@host_bp.route("/NITROG")
@admin_required
def serve_nitrog():
    bulk_path = os.path.join(os.path.dirname(app.instance_path), "bulk")
    csv_filepath = os.path.join(bulk_path, "SUS/LND/NITROG/Raw/SNM_raw.csv")
    return send_file(
        csv_filepath,
        mimetype="text/csv",
        as_attachment=True,
        download_name="NITROG-RAW-DATA.csv"  # Name for the downloaded file
    )
