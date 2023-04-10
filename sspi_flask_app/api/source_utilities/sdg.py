import json
import time
import requests

# Implement API Collection for https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1
def collectSDGIndicatorData(IndicatorCode):
    url_source = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=" + IndicatorCode
    """make API request"""
    data = requests.get(url_source).json()
    return data