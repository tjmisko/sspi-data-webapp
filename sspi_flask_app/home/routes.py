from flask import Blueprint
from flask import current_app as app

home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static'
)