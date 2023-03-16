import json
import time
import requests
from ..api import parse_json

def collectAvailableGeoAreas(indicator_code):
    """
    To collect the data, we need to know which countries for which data is available to call
    the data collection API

    Here we call the data availability API to check what data is available

    We process the request into a list of strings of m49 codes which we can feed into the data collection function
    """
    json_data = requests.get("https://unstats.un.org/sdgapi/v1/sdg/Indicator/" + indicator_code + "/GeoAreas").json()
    m49_list = []
    # add each geoAreaCode string to the m49_list to return
    for observation in json_data:
        # extract the m49_code from the json file
        m49_string = observation["geoAreaCode"]
        # fix issue where leading zeros have been chopped off from m49 codes
        while len(m49_string) < 3:
            m49_string = "0" + m49_string
        # add the fixed string to the list
        m49_list.append(m49_string)
    return m49_list

def collectSDGIndicatorData(indicator_code):
    """
    This function collects the data from the SDG database using the m49 code list we return in the previous function

    Notice how we've separated the logic of getting the codes from the logic of calling the data api once we have them.
    This allows us to write smaller chunks of code that are easier to test and reason about. 
    """
    base_url = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/Data?indicator=" + indicator_code
    m49_list = collectAvailableGeoAreas(indicator_code)
    big_observation_list = []
    # add on the timePeriod variables to the URL
    for year in range(2000,2023):
        base_url = base_url + "&timePeriod=" + str(year)
    # for each country in the m49 list, make a serparate call to the database
    for country in m49_list:
        country_url = base_url + "&areaCode=" + country
        json_data = requests.get(country_url).json()
        print(json_data)
        time.sleep(5)
        big_observation_list.append(json_data["data"])
    return big_observation_list