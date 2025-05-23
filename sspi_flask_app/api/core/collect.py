from flask import Blueprint, Response, current_app as app
from flask_login import login_required, current_user
import requests
import time
from sspi_flask_app.models.database import (
    sspi_raw_outcome_data
)
from sspi_flask_app.api.datasource.oecdstat import (
    collectOECDIndicator,
    collectOECDSDMXData,
    collectOECDSDMXFORAID
)
from sspi_flask_app.api.datasource.epi import collectEPIData
from sspi_flask_app.api.datasource.fao import collectUNFAOData
from sspi_flask_app.api.datasource.fsi import collectFSIdata
from sspi_flask_app.api.datasource.iea import collectIEAData
from sspi_flask_app.api.datasource.ilo import collectILOData
from sspi_flask_app.api.datasource.itu import collect_itu_data
from sspi_flask_app.api.datasource.prisonstudies import collectPrisonStudiesData
from sspi_flask_app.api.datasource.sdg import collectSDGIndicatorData
from sspi_flask_app.api.datasource.sipri import collectSIPRIdata
from sspi_flask_app.api.datasource.taxfoundation import collectTaxFoundationData
from sspi_flask_app.api.datasource.uis import collectUISdata
from sspi_flask_app.api.datasource.vdem import collectVDEMData
from sspi_flask_app.api.datasource.wef import collectWEFQUELEC
from sspi_flask_app.api.datasource.who import collectCSTUNTData, collectWHOdata
from sspi_flask_app.api.datasource.wid import collectWIDData
from sspi_flask_app.api.datasource.worldbank import collectWorldBankdata
from sspi_flask_app.api.core.countrychar import insert_pop_data

log = app.logger


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
    log.info("Running /api/v1/collect/BIODIV")
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/REDLST", methods=['GET'])
@login_required
def redlst():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("15.5.1", "REDLST", **kwargs)
    log.info("Running /api/v1/collect/REDLST")
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


@collect_bp.route("/DEFRST", methods=['GET'])
@login_required
def defrst():
    def collect_iterator(**kwargs):
        yield from collectUNFAOData("5110", "6717", "RL", "DEFRST", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/CARBON", methods=['GET'])
@login_required
def carbon():
    def collect_iterator(**kwargs):
        yield from collectUNFAOData("7215", "6646", "RL", "CARBON", **kwargs)
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
@login_required
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
        yield from collectIEAData("CO2BySector", "GTRANS", IntermediateCode="TCO2EQ", SourceOrganization="IEA", **kwargs)
        yield from collectWorldBankdata("SP.POP.TOTL", "GTRANS", IntermediateCode="POPULN", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/BEEFMK", methods=['GET'])
@login_required
def beefmk():
    def collect_iterator(**kwargs):
        # yield from collectUNFAOData("2312%2C2313", "1806%2C1746", "QCL", "BEEFMK", **kwargs)
        # yield from collectUNFAOData("C2510%2C2111%2C2413", "1806%2C1746", "QCL", "BEEFMK", **kwargs)
        # yield from collectWorldBankdata("SP.POP.TOTL", "BEEFMK", IntermediateCode="POPULN", **kwargs)
        yield from collectUNFAOData(
            "2910%2C645%2C2610%2C2510%2C511", "2731%2C2501",
            "FBS", "BEEFMK", **kwargs
        )
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


######################################################
### Collection Routes for Pillar: MARKET STRUCTURE ###
######################################################

#################################
## Category: WORKER ENGAGEMENT ##
#################################


@collect_bp.route("/EMPLOY")
@login_required
def lfpart():
    def collect_iterator(**kwargs):
        yield from collectILOData(
            "DF_EAP_DWAP_SEX_AGE_RT",
            "EMPLOY",
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


@collect_bp.route("/YRSEDU")
@login_required
def yrsedu():
    def collect_iterator(**kwargs):
        yield from collectUISdata("YEARS.FC.COMP.1T3", "YRSEDU", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


#################################
## Category: WORKER WELLBEING ##
################################


@collect_bp.route("/SENIOR")
@login_required
def senior():
    def collect_iterator(**kwargs):
        oecd_code = "OECD.ELS.SPD,DSD_PAG@DF_PAG"
        meta = (
            "https://sdmx.oecd.org/public/rest/datastructure/ALL/DSD_PAG/"
            "latest?references=all&format=sdmx-json"
        )
        yield from collectOECDSDMXData(oecd_code, "SENIOR", metadata_url=meta, **kwargs)
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

#####################
## Category: TAXES ##
#####################


@collect_bp.route("/TAXREV", methods=['GET'])
@login_required
def taxrev():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("GC.TAX.TOTL.GD.ZS", "TAXREV", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/CRPTAX", methods=['GET'])
@login_required
def crptax():
    def collect_iterator(**kwargs):
        yield from collectTaxFoundationData('CRPTAX', **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

################################
## Category: FINANCIAL SECTOR ##
################################


@collect_bp.route("/FDEPTH", methods=['GET'])
@login_required
def fdepth():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("FS.AST.PRVT.GD.ZS", "FDEPTH", IntermediateCode="CREDIT", **kwargs)
        yield from collectWorldBankdata("GFDD.OI.02", "FDEPTH", IntermediateCode="DPOSIT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/PUBACC", methods=['GET'])
@login_required
def pubacc():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("FX.OWN.TOTL.ZS", "PUBACC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


# @collect_bp.route("/FSTABL", methods=['GET'])
# def fstabl():
#     def collect_iterator(**kwargs):
# https://github.com/Promptly-Technologies-LLC/imfp --> imf api package

##########################
## Category: INEQUALITY ##
##########################
@collect_bp.route("/ISHRAT", methods=['GET'])
@login_required
def ishrat():
    def collect_iterator(**kwargs):
        yield from collectWIDData(IndicatorCode="ISHRAT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


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


@collect_bp.route("/ENRPRI", methods=['GET'])
@login_required
def enrpri():
    def collect_iterator(**kwargs):
        yield from collectUISdata("NERT.1.CP", "ENRPRI", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/ENRSEC", methods=['GET'])
@login_required
def enrsec():
    def collect_iterator(**kwargs):
        yield from collectUISdata("NERT.2.CP", "ENRSEC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/PUPTCH", methods=['GET'])
@login_required
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


# # PHYSPC for Correlation Analysis with UHC
# @collect_bp.route("/PHYSPC", methods=['GET'])
# @login_required
# def physpc():
#     def collect_iterator(**kwargs):
#         yield from collectWHOdata("UHC_INDEX_REPORTED", "PHYSPC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/PHYSPC", methods=['GET'])
@login_required
def physpc():
    def collect_iterator(**kwargs):
        yield from collectWHOdata("HWF_0001", "PHYSPC", **kwargs)
        yield from collectSDGIndicatorData("3.8.1", "PHYSPC", **kwargs)
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
        yield from collectSDGIndicatorData("17.6.1", "INTRNT", IntermediateCode="QUINTR", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/AQELEC", methods=['GET'])
@login_required
def aqelec():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("EG.ELC.ACCS.ZS", "AQELEC", IntermediateCode="AVELEC", **kwargs)
        yield from collectWEFQUELEC("WEF.GCIHH.EOSQ064", "AQELEC", IntermediateCode="QUELEC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


###########################
## Category: RIGHTS ##
###########################


@collect_bp.route("/RULELW", methods=['GET'])
@login_required
def rulelw():
    def collect_iterator(**kwargs):
        yield from collectVDEMData("v2x_rule", "RULELW", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/EDEMOC", methods=['GET'])
@login_required
def edemoc():
    def collect_iterator(**kwargs):
        yield from collectVDEMData("v2x_polyarchy", "EDEMOC", **kwargs)
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


@collect_bp.route("/CYBSEC", methods=['GET'])
@login_required
def cybsec():
    def collect_iterator(**kwargs):
        yield from collect_itu_data("CYBSEC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/SECAPP", methods=['GET'])
@login_required
def secapp():
    def collect_iterator(**kwargs):
        yield from collectFSIdata("SECAPP", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


###########################
## Category: GLOBAL ROLE ##
###########################


@collect_bp.route("/RDFUND", methods=['GET'])
@login_required
def rdfund():
    def collect_iterator(**kwargs):
        yield from collectSDGIndicatorData("9.5.1", "RDFUND", **kwargs)
        yield from collectSDGIndicatorData("9.5.2", "RDFUND", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/FORAID", methods=['GET'])
@login_required
def foraid():
    def collect_iterator(**kwargs):
        metadata_url = "https://sdmx.oecd.org/public/rest/dataflow/OECD.DCD.FSD/DSD_DAC2@DF_DAC2A/?references=all"
        yield from collectOECDSDMXFORAID("OECD.DCD.FSD,DSD_DAC2@DF_DAC2A,", "FORAID",
                                         filter_parameters="..206.USD.Q",
                                         metadata_url=metadata_url,
                                         IntermediateCode="ODAFLW", **kwargs)
        yield from collectWorldBankdata("SP.POP.TOTL", "FORAID", IntermediateCode="POPULN", **kwargs)
        yield from collectWorldBankdata("NY.GDP.MKTP.KD", "FORAID", IntermediateCode="GDPMKT", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/MILEXP", methods=['GET'])
@login_required
def milexp():
    def collect_iterator(**kwargs):
        yield from collectSIPRIdata("MILEXP", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@collect_bp.route("/ARMEXP", methods=['GET'])
@login_required
def armexp():
    def collect_iterator(**kwargs):
        yield from collectSIPRIdata("local/ARMEXP/armexp.csv", "ARMEXP", **kwargs)
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
        url_source = (
            "https://api.worldbank.org/v2/country/all/"
            f"indicator/{WorldBankIndicatorCode}?format=json"
        )
        response = requests.get(url_source).json()
        total_pages = response[0]['pages']
        for p in range(1, total_pages + 1):
            new_url = f"{url_source}&page={p}"
            yield f"Sending Request for page {p} of {total_pages}\n"
            response = requests.get(new_url).json()
            document_list = response[1]
            count = sspi_raw_outcome_data.raw_insert_many(
                document_list, IndicatorCode, **kwargs)
            yield f"Inserted {count} new observations into sspi_outcome_data\n"
            time.sleep(0.5)
        yield f"Collection complete for World Bank Indicator {WorldBankIndicatorCode}"

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
        url_source = (
            "https://api.worldbank.org/v2/country/all/"
            f"indicator/{WorldBankIndicatorCode}?format=json"
        )
        response = requests.get(url_source).json()
        total_pages = response[0]['pages']
        for p in range(1, total_pages + 1):
            new_url = f"{url_source}&page={p}"
            yield f"Sending Request for page {p} of {total_pages}\n"
            response = requests.get(new_url).json()
            document_list = response[1]
            count = sspi_raw_outcome_data.raw_insert_many(
                document_list, IndicatorCode, **kwargs)
            yield f"Inserted {count} new observations into sspi_outcome_data\n"
            time.sleep(0.5)
        yield "Collection complete for World Bank Indicator {WorldBankIndicatorCode}"

    def collect_iterator(**kwargs):
        # insert UN population data into sspi_country_characteristics database
        yield from collectWorldBankOutcomeData("NY.GDP.PCAP.PP.CD", "GDPPPP", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')
