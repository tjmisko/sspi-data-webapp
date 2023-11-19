from flask import Blueprint, render_template
from flask_login import login_required

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)

@api_bp.route("/", methods=["GET"])
@login_required
def api_dashboard():
    return render_template("internal-dashboard.html")
