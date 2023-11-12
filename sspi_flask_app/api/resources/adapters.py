from ..resources.utilities import parse_json
from ... import sspi_raw_api_data
from datetime import datetime

#############################
# Collect Storage Utilities #
#############################

def raw_insert_one(observation, IndicatorCode, IntermediateCode="NA", Metadata="NA"):
    """
    Utility Function the response from an API call in the database
    - Observation to be passed as a well-formed dictionary for entry into pymongo
    - IndicatorCode is the indicator code for the indicator that the observation is for
    """
    sspi_raw_api_data.insert_one({
        "collection-info": {
            "IndicatorCode": IndicatorCode,
            "IntermediateCodeCode": IntermediateCode,
            "Metadata": Metadata,
            "CollectedAt": datetime.now()
        },
        "observation": observation
    })
    return 1
    
def raw_insert_many(observation_list, IndicatorCode, IntermediateCode="NA", Metadata="NA"):
    """
    Utility Function 
    - Observation to be past as a list of well form observation dictionaries
    - IndicatorCode is the indicator code for the indicator that the observation is for
    """
    for i, observation in enumerate(observation_list):
        raw_insert_one(observation, IndicatorCode, IntermediateCode, Metadata)
    return i+1

def fetch_raw_data(IndicatorCode):
    """
    Utility function that handles querying the database
    """
    mongoQuery = {"collection-info.IndicatorCode": IndicatorCode}
    raw_data = parse_json(sspi_raw_api_data.find(mongoQuery))
    return raw_data

def raw_data_available(IndicatorCode):
    """
    Check if indicator is in database
    """
    return bool(sspi_raw_api_data.find_one({"collection-info.IndicatorCode": IndicatorCode}))