from ..resources.utilities import parse_json
from ... import sspi_raw_api_data
from datetime import datetime

#############################
# Collect Storage Utilities #
#############################

def raw_insert_one(observation, IndicatorCode, **kwargs):
    """
    Utility Function the response from an API call in the database
    - Observation to be passed as a well-formed dictionary for entry into pymongo
    - IndicatorCode is the indicator code for the indicator that the observation is for
    """
    document = {
        "IndicatorCode": IndicatorCode,
        "Raw": observation, 
        "CollectedAt": datetime.now()
    }
    document.update(kwargs)
    sspi_raw_api_data.insert_one(document)
    return 1
    
def raw_insert_many(observation_list, IndicatorCode, **kwargs):
    """
    Utility Function 
    - Observation to be past as a list of well form observation dictionaries
    - IndicatorCode is the indicator code for the indicator that the observation is for
    """
    for i, observation in enumerate(observation_list):
        raw_insert_one(observation, IndicatorCode, **kwargs)
    return i+1

def fetch_raw_data(IndicatorCode, **kwargs):
    """
    Utility function that handles querying the database
    """
    mongoQuery = {"IndicatorCode": IndicatorCode}
    mongoQuery.update(kwargs)
    return sspi_raw_api_data.find(mongoQuery)

def raw_data_available(IndicatorCode):
    """
    Check if indicator is in database
    """
    return bool(sspi_raw_api_data.find_one({"IndicatorCode": IndicatorCode}))
