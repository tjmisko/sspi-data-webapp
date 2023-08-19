from ... import sspi_raw_api_data
from flask import Blueprint, Response
from flask_login import login_required, current_user
from ..datasource.sdg import collectSDGIndicatorData
from ..datasource.iea import collectIEAData
from ..datasource.ilo import requestILO
from .dashboard import parse_json
from flask import redirect, url_for
from datetime import datetime

collect_bp = Blueprint("collect_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/collect")
#############################
# Collect Storage Utilities #
#############################

@collect_bp.route("/utility/raw_insert_one")
@login_required
def raw_insert_one(observation, RawDataDestination):
    """
    Utility Function the response from an API call in the database
    - Observation to be passed as a well-formed dictionary for entry into pymongo
    - RawDataDestination is the indicator code for the indicator that the observation is for
    """
    sspi_raw_api_data.insert_one(
    {"collection-info": {"CollectedBy": current_user,
                         "RawDataDestination": RawDataDestination,
                         "CollectedAt": datetime.now()}, 
    "observation": observation})

@collect_bp.route("/utility/raw_insert_many")
@login_required
def raw_insert_many(observation_list, RawDataDestination):
    """
    Utility Function 
    - Observation to be past as a list of well form observation dictionaries
    - RawDataDestination is the indicator code for the indicator that the observation is for
    """
    for observation in observation_list:
        raw_insert_one(observation, RawDataDestination)

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
    collectIEAData("TFCbySource", "ALTNRG")
    return "success!"

##################################################
# Collection Routes for Pillar: MARKET STRUCTURE #
##################################################

@collect_bp.route("/LFPART")
@login_required
def lfpart():
    def collect_iterator():
        yield from requestILO("DF_EAP_DWAP_SEX_AGE_RT", "LFPART")
    return Response(collect_iterator(), mimetype='text/event-stream')