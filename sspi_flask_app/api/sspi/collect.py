from flask import Blueprint
from flask_login import login_required
from ..source_utilities.sdg import collectSDGIndicatorData
from ..source_utilities.iea import collectIEAData
from ..api import parse_json
from flask import redirect, url_for
import datetime
import requests


collect_bp = Blueprint("collect_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/collect")

@collect_bp.route("/BIODIV", methods=['GET'])
@login_required
def biodiv():
    collectSDGIndicatorData("14.5.1", "BIODIV")
    collectSDGIndicatorData("15.1.2", "BIODIV")
    return "success!"

@collect_bp.route("REDLST", methods=['GET'])
@login_required
def redlst():
    collectSDGIndicatorData("15.5.1", "REDLST")
    return "success!"

@collect_bp.route("STKHLM", methods=['GET'])
@login_required
def stkhlm():
    return collectSDGIndicatorData("12.4.1", "STKHLM")
    
@collect_bp.route("COALPW", methods=['GET'])
@login_required
def coalpw():
    collectIEAData("TESbySource", "COALPW")
    return "success!"
