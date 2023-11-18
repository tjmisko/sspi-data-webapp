from flask import Blueprint
from flask_login import login_required

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)


@api_bp.route("/")
@login_required
def index():
    return "Hello World!"