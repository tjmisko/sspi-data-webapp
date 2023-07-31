import json
import time
import requests
import math

from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime
from pycountry import countries


#https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/QNA/all/OECD

#figure out database identifier "QNA"