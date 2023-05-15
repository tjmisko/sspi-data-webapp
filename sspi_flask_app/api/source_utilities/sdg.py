import json
import time
import requests
from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime

# Implement API Collection for https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1
def collectSDGIndicatorData(SDGIndicatorCode, RawDataDestination):
    collection_time = datetime.now()
    url_source = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=" + SDGIndicatorCode
    response = requests.get(url_source)
    nPages = response.json().get('totalPages')
    for p in range(1, nPages + 1):
        new_url = url_source+ "&page=" + str(p)
        print(new_url)
        response = requests.get(new_url)
        for r in response.json().get('data'):
            sspi_raw_api_data.insert_one(
                {"collection-info": {"CollectedBy": current_user.username,
                                    "RawDataDestination": RawDataDestination,
                                    "CollectedAt": collection_time}, 
                "observation": r}
            )
        time.sleep(0.5)
    return response

