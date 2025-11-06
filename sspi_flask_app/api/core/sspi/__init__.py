import time
from flask import Blueprint, current_app as app, Response
from flask_login import login_required
from connector import SSPIDatabaseConnector
from sspi_flask_app.models.database import sspi_metadata

compute_bp = Blueprint(
    "compute_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/compute",
)

impute_bp = Blueprint(
    "impute_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/impute",
)

@compute_bp.route("/<series_code>", methods=["POST"])
@login_required
def compute_series(series_code):
    def compute_iterator(series_code, endpoints):
        if series_code.upper() == "ALL":
            series_code = "SSPI"
        indicator_codes = sspi_metadata.get_indicator_dependencies(series_code)
        connector = SSPIDatabaseConnector()
        for ic in indicator_codes:
            if f"api_bp.compute_bp.compute_{ic.lower()}" in endpoints:
                res = connector.call(f"/api/v1/compute/{ic}", method="POST")
                yield f"Compute {ic}: {res.status_code}\n"
        return "Computation Complete"

    endpoints = [str(r.endpoint) for r in app.url_map.iter_rules()]
    return Response(compute_iterator(series_code, endpoints), mimetype="text/event-stream")

@impute_bp.route("/<series_code>", methods=["POST"])
@login_required
def impute_all(series_code):
    def impute_iterator(series_code, endpoints):
        if series_code.upper() == "ALL":
            series_code = "SSPI"
        indicator_codes = sspi_metadata.get_indicator_dependencies(series_code)
        connector = SSPIDatabaseConnector()
        for ic in indicator_codes:
            if f"api_bp.impute_bp.impute_{ic.lower()}" in endpoints:
                res = connector.call(f"/api/v1/impute/{ic}", method="POST")
                yield f"Impute {ic}: {res.status_code}\n"
            else:
                yield f"No Impute route for {ic}"
        return "Imputation Complete"

    endpoints = [str(r.endpoint) for r in app.url_map.iter_rules()]
    return Response(impute_iterator(series_code, endpoints), mimetype="text/event-stream")
