import json
import time
import requests
import math
import pandasdmx as sdmx
import pandas as pd

from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime
from pycountry import countries
from ..api import format_m49_as_string
from ..api import string_to_float

def collectOECDIndicator(SDMX_URL, RawDataDestination):
    response_obj = requests.get(SDMX_URL)
    print("RawDataDestination: {}".format(RawDataDestination))
    print(response_obj.status_code)
    print(response_obj.headers)
    print(response_obj.content)
    return "hello"