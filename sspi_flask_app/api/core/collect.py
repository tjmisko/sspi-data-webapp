from ... import sspi_raw_api_data
from flask import Blueprint, Response
from flask_login import login_required, current_user

from ..datasource.oecdstat import collectOECDIndicator
from ..datasource.worldbank import collectWorldBankdata
from ..datasource.sdg import collectSDGIndicatorData
from ..datasource.iea import collectIEAData
# from ..datasource.ilo import requestILO
from ..datasource.prisonstudies import collectPrisonStudiesData
from .dashboard import parse_json
from flask import redirect, url_for
from datetime import datetime

collect_bp = Blueprint("collect_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/collect")

################################################
# Collection Routes for Pillar: SUSTAINABILITY #
################################################

###########################
### Category: ECOSYSTEM ###
###########################

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

######################
### Category: LAND ###
######################

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

####################
# Category: ENERGY #
####################

@collect_bp.route("/COALPW", methods=['GET'])
@login_required
def coalpw():
    def collect_iterator():
        yield from collectIEAData("TESbySource", "COALPW")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/ALTNRG", methods=['GET'])
@login_required
def altnrg():
    def collect_iterator():
        yield from collectIEAData("TESbySource", "ALTNRG")
    return Response(collect_iterator(), mimetype='text/event-stream') 

##################################################
# Collection Routes for Pillar: MARKET STRUCTURE #
##################################################

# @collect_bp.route("/LFPART")
# @login_required
# def lfpart():
    # def collect_iterator():
        # yield from requestILO("DF_EAP_DWAP_SEX_AGE_RT", "LFPART")
    # return Response(collect_iterator(), mimetype='text/event-stream')
    
@collect_bp.route("/GTRANS", methods=['GET'])
# @login_required
def gtrans():
    def collect_iterator():
        yield from collectOECDIndicator("AIR_GHG", "GTRANS")
        yield from collectIEAData("CO2Emissions", "GTRANS")
        # yield from collectWorldBankdata("EP.PMP.SGAS.CD", "GTRANS")
    return Response(collect_iterator(), mimetype='text/event-stream') 

@collect_bp.route("/GINIPT", methods=['GET'])
def ginipt():
    def collect_iterator():  
        yield from collectWorldBankdata("SI.POV.GINI", "GINIPT")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/PRISON", methods=['GET'])
@login_required
def prison():
    def collect_iterator():
        yield from collectPrisonStudiesData()
    return Response(collect_iterator(), mimetype='text/event-stream')