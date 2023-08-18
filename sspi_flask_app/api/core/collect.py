from flask import Blueprint, Response
from flask_login import login_required, current_user
from ..datasource.sdg import collectSDGIndicatorData
from ..datasource.iea import collectIEAData
from ..datasource.ilo import requestILO
from .dashboard import parse_json
from flask import redirect, url_for
import datetime
import requests
import time

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
        yield "data: Collection complete"
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/REDLST", methods=['GET'])
@login_required
def redlst():
    def collect_iterator():
        yield from collectSDGIndicatorData("15.5.1", "REDLST")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/WATMAN", methods=['GET'])
@login_required
def watman():
    def collect_iterator():
        yield from collectSDGIndicatorData("6.4.1", "WATMAN")
        yield from collectSDGIndicatorData("6.4.2", "WATMAN")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/STKHLM", methods=['GET'])
@login_required
def stkhlm():
    def collect_iterator():
        yield from collectSDGIndicatorData("12.4.1", "STKHLM")
    return Response(collect_iterator(), mimetype='text/event-stream')
    
@collect_bp.route("/COALPW", methods=['GET'])
@login_required
def coalpw():
    def collect_iterator():
        yield from collectIEAData("TESbySource", "COALPW")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/ALTNRG", methods=['GET'])
@login_required
def altnrg():
    collectIEAData("TFCbySource", "ALTNRG")
    return "success!"

@collect_bp.route("/LFPART")
@login_required
def lfpart():
    def collect_iterator():
        yield from requestILO("DF_EAP_DWAP_SEX_AGE_RT", "LFPART")
    return Response(collect_iterator(), mimetype='text/event-stream')