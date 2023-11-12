from ... import sspi_raw_api_data
from flask import Blueprint, Response
from flask_login import login_required

from ..datasource.oecdstat import collectOECDIndicator
from ..datasource.worldbank import collectWorldBankdata
from ..datasource.sdg import collectSDGIndicatorData
from ..datasource.iea import collectIEAData
from ..datasource.ilo import collectILOData
from ..datasource.prisonstudies import collectPrisonStudiesData
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

@collect_bp.route("/NRGINT", methods=['GET'])
@login_required
def nrgint():
    def collect_iterator():
        yield from collectSDGIndicatorData("7.3.1", "NRGINT")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/COALPW", methods=['GET'])
@login_required
def coalpw():
    def collect_iterator():
        yield from collectIEAData("TESbySource", "COALPW")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/AIRPOL", methods=['GET'])
@login_required
def airpol():
    def collect_iterator():
        yield from collectSDGIndicatorData("11.6.2", "AIRPOL")
    return Response(collect_iterator(), mimetype='text/event-stream')

@collect_bp.route("/ALTNRG", methods=['GET'])
@login_required
def altnrg():
    def collect_iterator():
        yield from collectIEAData("TESbySource", "ALTNRG")
    return Response(collect_iterator(), mimetype='text/event-stream') 

@collect_bp.route("/GTRANS", methods=['GET'])
# @login_required
def gtrans():
    def collect_iterator():
        # yield from collectOECDIndicator("AIR_GHG", "GTRANS", "TCO2EQ-OECD")
        yield from collectOECDIndicator("AIR_GHG", "GTRANS", "TCO2EQ-OECD")
        yield from collectIEAData("CO2BySector", "GTRANS", "TCO2EQ-IEA")
        yield from collectWorldBankdata("EP.PMP.SGAS.CD", "GTRANS", "FUELPR")
    return Response(collect_iterator(), mimetype='text/event-stream') 

##################################################
# Collection Routes for Pillar: MARKET STRUCTURE #
##################################################

@collect_bp.route("/LFPART")
@login_required
def lfpart():
    def collect_iterator():
        yield from collectILOData("DF_EAP_DWAP_SEX_AGE_RT", "LFPART", ".A...AGE_AGGREGATE_Y25-54")
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

@collect_bp.route("/FDEPTH", methods=['GET'])
def fdepth():
    def collect_iterator():  
        yield from collectWorldBankdata("FS.AST.PRVT.GD.ZS", "FDEPTH", "CREDIT")
        yield from collectWorldBankdata("GFDD.OI.02", "FDEPTH", "DPOSIT")                                        
    return Response(collect_iterator(), mimetype='text/event-stream')


#############################
# Collect Storage Utilities #
#############################

def raw_insert_one(observation, IndicatorCode, IntermediateCode="NA", Metadata="NA"):
    """
    Utility Function the response from an API call in the database
    - Observation to be passed as a well-formed dictionary for entry into pymongo
    - IndicatorCode is the indicator code for the indicator that the observation is for
    """
    sspi_raw_api_data.insert_one({
        "collection-info": {
            "IndicatorCode": IndicatorCode,
            "IntermediateCodeCode": IntermediateCode,
            "Metadata": Metadata,
            "CollectedAt": datetime.now()
        },
        "observation": observation
    })
    return 1
    
def raw_insert_many(observation_list, IndicatorCode, IntermediateCode="NA", Metadata="NA"):
    """
    Utility Function 
    - Observation to be past as a list of well form observation dictionaries
    - IndicatorCode is the indicator code for the indicator that the observation is for
    """
    for i, observation in enumerate(observation_list):
        raw_insert_one(observation, IndicatorCode, IntermediateCode, Metadata)
    return i+1