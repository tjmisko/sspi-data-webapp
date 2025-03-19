from flask import Blueprint

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates",
                       static_folder="static",
                       url_prefix="/compute")
