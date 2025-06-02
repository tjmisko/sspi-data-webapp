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
