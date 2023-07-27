from flask import Blueprint, Response
from flask_login import login_required, current_user
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
    def collect_iterator():
        yield from collectSDGIndicatorData("14.5.1", "BIODIV")
        yield from collectSDGIndicatorData("15.1.2", "BIODIV")
        yield "Collection complete"
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("REDLST", methods=['GET'])
@login_required
def redlst():
    collectSDGIndicatorData("15.5.1", "REDLST")
    return "success!"

@collect_bp.route("WATMAN", methods=['GET'])
@login_required
def watman():
    collectSDGIndicatorData("6.4.1", "WATMAN")
    collectSDGIndicatorData("6.4.2", "WATMAN")
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

@collect_bp.route("ALTNRG", methods=['GET'])
@login_required
def altnrg():
    collectIEAData("TFCbySource", "ALTNRG")
    return "success!"
