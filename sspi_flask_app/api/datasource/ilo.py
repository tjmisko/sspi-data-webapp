from ... import sspi_raw_api_data
import pandasdmx as sdmx
import pandas as pd
import json

def requestILO(ILOIndicatorCode, RawDataDestination):
    return sdmx.Request('ILO')
    