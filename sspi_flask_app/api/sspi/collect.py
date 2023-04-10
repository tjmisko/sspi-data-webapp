from flask import Blueprint


collect_bp = Blueprint("collect_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/collect")

@collect_bp.route("/BIODIV", methods=['GET'])
def biodiv():
    return "BIODIV"