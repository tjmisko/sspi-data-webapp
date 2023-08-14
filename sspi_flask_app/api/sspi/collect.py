from flask import Blueprint, Response
from flask_login import login_required, current_user
from ..source_utilities.sdg import collectSDGIndicatorData
from ..source_utilities.iea import collectIEAData
from ..source_utilities.oecdstat import collectOECDIndicator
from ..api import parse_json
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
    def test_generator():
        for i in range(10):
            message = "data: {}\n".format(i)
            yield message
            print(message)
            time.sleep(2)
        yield "data: close"
    return Response(test_generator(), mimetype='text/event-stream')

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

@collect_bp.route("GTRANS", methods=['GET'])
# @login_required
def gtrans():
    SDMX_URL_OECD = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/AIR_GHG/AUS+AUT+BEL+CAN+CHL+COL+CRI+CZE+DNK+EST+FIN+FRA+DEU+GRC+HUN+ISL+IRL+ISR+ITA+JPN+KOR+LVA+LTU+LUX+MEX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+SWE+CHE+TUR+GBR+USA+NMEC+ARG+BGD+BLR+BRA+BGR+CHN+HRV+CYP+IND+IDN+IRN+KAZ+LIE+MLT+MCO+PER+ROU+RUS+SAU+ZAF+UKR+OECDAM+OECDAO.GHG+CO2.TOTAL+ENER+ENER_IND+ENER_MANUF+ENER_TRANS+ENER_OSECT+ENER_OTH+ENER_FU+ENER_CO2+TOTAL_LULU+INTENS+GHG_CAP+GHG_GDP+GHG_CAP_LULU+GHG_GDP_LULU+INDEX+INDEX_2000+INDEX_1990+PERCENT+ENER_P+ENER_IND_P+ENER_MANUF_P+ENER_TRANS_P+ENER_OSECT_P+ENER_OTH_P+ENER_FU_P+ENER_CO2_P+IND_PROC_P+AGR_P+WAS_P+OTH_P/all?startTime=1990&endTime=2021"
    collectOECDIndicator(SDMX_URL_OECD, "GTRANS")
    return "success!"