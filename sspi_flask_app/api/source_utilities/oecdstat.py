import json
import time
import requests
import math

from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime
from pycountry import countries
from ..api import format_m49_as_string
from ..api import string_to_float

def collectOECDIndicator(SDMX_URL, RawDataDestination):
    xml_data = requests.get(SDMX_URL)
    print(xml_data.json())