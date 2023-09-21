from ... import sspi_raw_api_data
from flask import Blueprint, Response
from flask_login import login_required, current_user

from ..datasource.oecdstat import collectOECDIndicator
from ..datasource.worldbank import collectWorldBankdata
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
    collectIEAData("TESbySource", "ALTNRG")
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
    
@collect_bp.route("GTRANS", methods=['GET'])
# @login_required
def gtrans():
    SDMX_URL_OECD = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/AIR_GHG/AUS+AUT+BEL+CAN+CHL+COL+CRI+CZE+DNK+EST+FIN+FRA+DEU+GRC+HUN+ISL+IRL+ISR+ITA+JPN+KOR+LVA+LTU+LUX+MEX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+SWE+CHE+TUR+GBR+USA+NMEC+ARG+BGD+BLR+BRA+BGR+CHN+HRV+CYP+IND+IDN+IRN+KAZ+LIE+MLT+MCO+PER+ROU+RUS+SAU+ZAF+UKR+OECDAM+OECDAO.GHG+CO2.TOTAL+ENER+ENER_IND+ENER_MANUF+ENER_TRANS+ENER_OSECT+ENER_OTH+ENER_FU+ENER_CO2+TOTAL_LULU+INTENS+GHG_CAP+GHG_GDP+GHG_CAP_LULU+GHG_GDP_LULU+INDEX+INDEX_2000+INDEX_1990+PERCENT+ENER_P+ENER_IND_P+ENER_MANUF_P+ENER_TRANS_P+ENER_OSECT_P+ENER_OTH_P+ENER_FU_P+ENER_CO2_P+IND_PROC_P+AGR_P+WAS_P+OTH_P/all?startTime=1990&endTime=2021"
    collectOECDIndicator(SDMX_URL_OECD, "GTRANS")
    collectWorldBankdata("EP.PMP.SGAS.CD", "GTRANS")
    return "success!"
