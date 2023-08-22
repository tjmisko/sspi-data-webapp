from ..api import parse_json
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
    meta = ilo.datastructure(ILOIndicatorCode)
    yield "SDMX Metadata:\n"
    yield str(meta)
    yield str("Ref Area: {0}".format())
    yield str(sdmx.to_pandas(meta.codelist))
    print("getting data!")
    data = ilo.data(ILOIndicatorCode, key={"AGE": "AGE_AGGREGATE_Y25-54",
                                           "FREQ": "A",
                                           "SEX": "T"})
    print(data)
    yield "SDMX CodeList:\n"
    yield sdmx.to_pandas(meta.codelist)
    yield sdmx.to_pandas(data)
    yield "Collection Complete!"