import pandas as pd
import requests


def collectIEAData(IndicatorCode):
    response = requests.get("https://api.iea.org/stats/indicator/" + IndicatorCode + "/").json()
    return response
   
def compute_altnrg(): 
    raw_data = collectIEAData("TFCbySource")
    return pd.DataFrame(raw_data)
