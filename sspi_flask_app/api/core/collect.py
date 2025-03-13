from flask import Blueprint, Response
from flask_login import login_required, current_user
import requests
import time

from sspi_flask_app.api.datasource.oecdstat import collectOECDIndicator, collectOECDSDMXData
from sspi_flask_app.api.datasource.epi import collectEPIData
from sspi_flask_app.api.datasource.worldbank import collectWorldBankdata
from sspi_flask_app.api.datasource.sdg import collectSDGIndicatorData
from sspi_flask_app.api.datasource.iea import collectIEAData
from sspi_flask_app.api.datasource.wef import collectWEFQUELCT
from sspi_flask_app.api.datasource.ilo import collectILOData
from sspi_flask_app.api.datasource.who import collectWHOdata
from sspi_flask_app.api.datasource.prisonstudies import collectPrisonStudiesData
from sspi_flask_app.api.datasource.who import collectCSTUNTData

from .countrychar import insert_pop_data
from sspi_flask_app.models.database import (
    sspi_raw_outcome_data,
    sspi_clean_outcome_data
)


collect_bp = Blueprint("collect_bp", __name__,
                       template_folder="templates",
                       static_folder="static",
                       url_prefix="/collect")

####################################################
### Collection Routes for Pillar: SUSTAINABILITY ###
####################################################

#########################
## Category: ECOSYSTEM ##
#########################


@collect_bp.route("/BIODIV", methods=['GET'])
@login_required
def biodiv():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("14.5.1", "BIODIV", IntermediateCode="MARINE", **kwargs)
        yield from collectSDGIndicatorData("15.1.2", "BIODIV", Metadata="TERRST,FRSHWT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/REDLST", methods=['GET'])
@login_required
def redlst():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("15.5.1", "REDLST", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


####################
## Category: LAND ##
####################


@collect_bp.route("/NITROG", methods=['GET'])
@login_required
def nitrog():
    def collect_iterator(**kwargs):
        yield from collectEPIData("SNM_ind_na.csv", "NITROG", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/WATMAN", methods=['GET'])
@login_required
def watman():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("6.4.1", "WATMAN", IntermediateCode="CWUEFF", **kwargs)
        yield from collectSDGIndicatorData("6.4.2", "WATMAN", IntermediateCode="WTSTRS", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/STKHLM", methods=['GET'])
@login_required
def stkhlm():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("12.4.1", "STKHLM", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

######################
## Category: ENERGY ##
######################


@collect_bp.route("/NRGINT", methods=['GET'])
@login_required
def nrgint():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("7.3.1", "NRGINT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/AIRPOL", methods=['GET'])
@login_required
def airpol():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("11.6.2", "AIRPOL", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/ALTNRG", methods=['GET'])
def altnrg():
    def collect_iterator(**kwargs):
        yield from collectIEAData("TESbySource", "ALTNRG", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

################################
## Category: GREENHOUSE GASES ##
################################


@collect_bp.route("/COALPW", methods=['GET'])
@login_required
def coalpw():
    def collect_iterator(**kwargs):
        yield from collectIEAData("TESbySource", "COALPW", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/GTRANS", methods=['GET'])
@login_required
def gtrans():
    def collect_iterator(**kwargs):
        # yield from collectIEAData("CO2BySector", "GTRANS", IntermediateCode="TCO2EQ", SourceOrganization="IEA", **kwargs)
        yield from collectWorldBankdata("EP.PMP.SGAS.CD", "GTRANS", IntermediateCode="FUELPR", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

######################################################
### Collection Routes for Pillar: MARKET STRUCTURE ###
######################################################

#################################
## Category: WORKER ENGAGEMENT ##
#################################


@collect_bp.route("/LFPART")
@login_required
def lfpart():
    def collect_iterator(**kwargs):
        yield from collectILOData(
            "DF_EAP_DWAP_SEX_AGE_RT",
            "LFPART",
            QueryParams=".A...AGE_AGGREGATE_Y25-54",
            **kwargs
        )
    return Response(
        collect_iterator(Username=current_user.username),
        mimetype='text/event-stream'
    )


@collect_bp.route("/COLBAR")
@login_required
def colbar():
    def collect_iterator(**kwargs):
        url_params = ["startPeriod=1990-01-01", "endPeriod=2024-12-31"]
        yield from collectILOData("DF_ILR_CBCT_NOC_RT", "COLBAR", URLParams=url_params, **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/CHILDW")
@login_required
def childw():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("4.1.1", "CHILDW", IntermediateCode="YSCEDU", **kwargs)
        yield from collectSDGIndicatorData("8.7.1", "CHILDW", IntermediateCode="CHLDLB", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

#################################
## Category: WORKER WELLBEING ##
################################


@collect_bp.route("/SENIOR")
@login_required
def senior():
    def collect_iterator(**kwargs):
        yield from collectOECDIndicator("PAG", "SENIOR", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/UNEMPL")
@login_required
def unempl():
    def collect_iterator(**kwargs):
        yield from collectILOData("DF_SDG_0131_SEX_SOC_RT", "UNEMPL", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/FATINJ")
@login_required
def fatinj():
    def collect_iterator(**kwargs):
        yield from collectILOData("DF_SDG_F881_SEX_MIG_RT", "FATINJ", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

@collect_bp.route("/MATERN")
@login_required
def matern():
    def collect_iterator(**kwargs):  # C1_4
        for chunk in collectOECDIndicator("OECD.WISE.CWB,DSD_CWB@DF_CWB", "MATERN", **kwargs):
            yield chunk.encode('utf-8') if isinstance(chunk, str) else chunk  # Convert strings to bytes
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

#####################
## Category: TAXES ##
#####################


@collect_bp.route("/TAXREV", methods=['GET'])
def taxrev():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("GC.TAX.TOTL.GD.ZS", "TAXREV", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

################################
## Category: FINANCIAL SECTOR ##
################################

@collect_bp.route("/FDEPTH", methods=['GET'])
def fdepth():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("FS.AST.PRVT.GD.ZS", "FDEPTH", IntermediateCode="CREDIT", **kwargs)
        yield from collectWorldBankdata("GFDD.OI.02", "FDEPTH", IntermediateCode="DPOSIT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

@collect_bp.route("/PUBACC", methods=['GET'])
def pubacc():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("FX.OWN.TOTL.ZS", "PUBACC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

# @collect_bp.route("/FSTABL", methods=['GET'])
# def fstabl():
#     def collect_iterator(**kwargs):

##########################
## Category: INEQUALITY ##
##########################


@collect_bp.route("/GINIPT", methods=['GET'])
@login_required
def ginipt():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("SI.POV.GINI", "GINIPT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

##################################################
### Collection Routes for Pillar: PUBLIC GOODS ###
##################################################

#########################
## Category: EDUCATION ##
#########################


@collect_bp.route("/PUPTCH", methods=['GET'])
def puptch():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("SE.PRM.ENRL.TC.ZS", "PUPTCH", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

##########################
## Category: HEALTHCARE ##
##########################


@collect_bp.route("/ATBRTH", methods=['GET'])
@login_required
def atbrth():
    def collect_iterator(**kwargs):
        yield from collectWHOdata("MDG_0000000025", "ATBRTH", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/DPTCOV", methods=['GET'])
@login_required
def dptcov():
    def collect_iterator(**kwargs):
        yield from collectWHOdata("vdpt", "DPTCOV", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/PHYSPC", methods=['GET'])
@login_required
def physpc():
    def collect_iterator(**kwargs):
        yield from collectWHOdata("HWF_0001", "PHYSPC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/FAMPLN", methods=['GET'])
@login_required
def fampln():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("3.7.1", "FAMPLN", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/CSTUNT", methods=['GET'])
@login_required
def cstunt():
    def collect_iterator(**kwargs):
        yield from collectCSTUNTData(**kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


##############################
## Category: INFRASTRUCTURE ##
##############################
@collect_bp.route("/DRKWAT", methods=['GET'])
@login_required
def drkwat():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("SH.H2O.SMDW.ZS", "DRKWAT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/SANSRV", methods=['GET'])
@login_required
def sansrv():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("SH.STA.BASS.ZS", "SANSRV", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/INTRNT", methods=['GET'])
@login_required
def intrnt():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("IT.NET.USER.ZS", "INTRNT", IntermediateCode="AVINTR", **kwargs)
        yield from collectSDGIndicatorData("17.6.1", "INTRNT", IntermediateCode="QLMBPS", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/AQELEC", methods=['GET'])
@login_required
def aqelec():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("EG.ELC.ACCS.ZS", "AQELEC", IntermediateCode="AVELEC", **kwargs)
        yield from collectWEFQUELCT("WEF.GCIHH.EOSQ064", "AQELEC", IntermediateCode="QUELCT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


#############################
## Category: PUBLIC SAFETY #
#############################


@collect_bp.route("/PRISON", methods=['GET'])
@login_required
def prison():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("SP.POP.TOTL", "PRISON", IntermediateCode="UNPOPL", **kwargs)
        yield from collectPrisonStudiesData(IntermediateCode="PRIPOP", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

###########################
## Category: GLOBAL ROLE ##
###########################


@collect_bp.route("/RDFUND", methods=['GET'])
@login_required
def rdfund():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("9.5.1", "RDFUND", IntermediateCode="GVTRDP,EDURDP,NRSRCH", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/FORAID", methods=['GET'])
@login_required
def foraid():
    def collect_iterator(**kwargs):
        metadata_url = "https://sdmx.oecd.org/public/rest/dataflow/OECD.DCD.FSD/DSD_DAC2@DF_DAC2A/?references=all"
        yield from collectOECDSDMXData("OECD.DCD.FSD,DSD_DAC2@DF_DAC2A,/.DPGC.206.USD.Q",
                                       "FORAID", metadata_url=metadata_url, **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


#######################################
## Category: Country Characteristics ##
#######################################
@collect_bp.route("/characteristic/UNPOPL", methods=['GET'])
@login_required
def unpopl():
    def collect_iterator(**kwargs):
        # insert UN population data into sspi_country_characteristics database
        yield from insert_pop_data()
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/outcome/GDPMER", methods=['GET'])
@login_required
def gdpmek():
    """Collect GDP per Capita at Market Exchange Rate from World Bank API"""
    def collectWorldBankOutcomeData(WorldBankIndicatorCode, IndicatorCode, **kwargs):
        yield "Collecting data for World Bank Indicator" + \
            "{WorldBankIndicatorCode}\n"
        url_source = f"https://api.worldbank.org/v2/country/all/indicator/{
            WorldBankIndicatorCode}?format=json"
        response = requests.get(url_source).json()
        total_pages = response[0]['pages']
        for p in range(1, total_pages+1):
            new_url = f"{url_source}&page={p}"
            yield f"Sending Request for page {p} of {total_pages}\n"
            response = requests.get(new_url).json()
            document_list = response[1]
            count = sspi_raw_outcome_data.raw_insert_many(
                document_list, IndicatorCode, **kwargs)
            yield f"Inserted {count} new observations into sspi_outcome_data\n"
            time.sleep(0.5)
        yield "Collection complete for World Bank Indicator" + \
            WorldBankIndicatorCode

    def collect_iterator(**kwargs):
        # insert UN population data into sspi_country_characteristics database
        yield from collectWorldBankOutcomeData("NY.GDP.PCAP.CD", "GDPMER", **kwargs)

    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/outcome/GDPPPP", methods=['GET'])
@login_required
def gdpppp():
    """Collect GDP per Capita at Market Exchange Rate from World Bank API"""
    def collectWorldBankOutcomeData(WorldBankIndicatorCode, IndicatorCode, **kwargs):
        yield "Collecting data for World Bank Indicator" + \
            "{WorldBankIndicatorCode}\n"
        url_source = f"https://api.worldbank.org/v2/country/all/indicator/{
            WorldBankIndicatorCode}?format=json"
        response = requests.get(url_source).json()
        total_pages = response[0]['pages']
        for p in range(1, total_pages+1):
            new_url = f"{url_source}&page={p}"
            yield f"Sending Request for page {p} of {total_pages}\n"
            response = requests.get(new_url).json()
            document_list = response[1]
            count = sspi_raw_outcome_data.raw_insert_many(
                document_list, IndicatorCode, **kwargs)
            yield f"Inserted {count} new observations into sspi_outcome_data\n"
            time.sleep(0.5)
        yield "Collection complete for World Bank Indicator" + \
            WorldBankIndicatorCode

    def collect_iterator(**kwargs):
        # insert UN population data into sspi_country_characteristics database
        yield from collectWorldBankOutcomeData("NY.GDP.PCAP.PP.CD", "GDPPPP", **kwargs)

    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')
