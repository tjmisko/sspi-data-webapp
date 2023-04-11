from flask import Blueprint
from ..source_utilities.sdg import collectSDGIndicatorData
from ..api import parse_json
collect_bp = Blueprint("collect_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/collect")

@collect_bp.route("/BIODIV", methods=['GET'])
def biodiv():
    collectSDGIndicatorData("14.5.1", "BIODIV")
    collectSDGIndicatorData("15.2.1", "BIODIV")
    return "success!"

@collect_bp.route("REDLST", methods=['GET'])
def redlst():
    collectSDGIndicatorData("15.5.1", "REDLST")
    return "success!"

@collect_bp.route("NITROG", methods=['GET'])
def nitrog():
    return "no collection route implemented"

@collect_bp.route("WATMAN", methods=['GET'])
def watman():
    return "no collection route implemented"

@collect_bp.route("STKHLM", methods=['GET'])
def stkhlm():
    return collectSDGIndicatorData("12.4.1", "STKHLM")
    
