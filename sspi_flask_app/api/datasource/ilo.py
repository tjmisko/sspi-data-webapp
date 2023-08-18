from ... import sspi_raw_api_data
import pandasdmx as sdmx
import pandas as pd
import json

def collectILOIndicatorData(ILOIndicatorCode, RawDataDestination):
    SDMX_meta = "url_here"
    SDMX_data = "https://www.ilo.org/sdmx/rest/data/ILO,DF_EAP_DWAP_SEX_AGE_RT/?format=jsondata&startPeriod=1990-01-01&endPeriod=2023-12-31"
    """call the apis with get requests---actually, check into the sdmx_package"""
    """for sdmx, keep the data in one observation and the meta needed for processing in the other"""
    """store_raw"""
    ilo = sdmx.Request('ILO')
    meta = ilo.datastructure('DF_EAP_DWAP_SEX_AGE_RT')
    print(meta)
    yield "Collection Complete!"