from flask import Blueprint, send_file
from flask_login import login_required
import os

host_bp = Blueprint(
    "host_bp", __name__,
    template_folder="templates",
    static_folder="static", 
    url_prefix="/bulk"
)


@host_bp.route("/NITROG")
def serve_nitrog():
    bulk_path = os.path.join(os.path.dirname(app.instance_path), "bulk")
    csv_filepath = os.path.join(bulk_path, "SUS/LND/NITROG/Raw/SNM_raw.csv")
    return send_file(
        csv_filepath,
        mimetype="text/csv",
        as_attachment=True,
        download_name="file.csv"  # Name for the downloaded file
    )
