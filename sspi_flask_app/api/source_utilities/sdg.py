import json
import requests
from ..api import parse_json

def collectAvailableGeoAreas(indicator_code):
    """
    To collect the data, we need to know which countries it is available for

    """
    json_data = requests.get("https://unstats.un.org/sdgapi/v1/sdg/Indicator/" + indicator_code + "/GeoAreas").json()
    m49_list = []
    for observation in json_data:
        m49_list.append(observation["geoAreaCode"])
    return m49_list

def collectSDGIndicatorData(indicator_code):
    """
    This function collects the data from the SDG database

    """
    base_url = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/Data?indicator=" + indicator_code
    m49_list = collectAvailableGeoAreas(indicator_code)
    big_json = {}
    for year in range(2000,2023):
        slug = "&timePeriod=" + str(year)
        for country in m49_list:
            if int(country) >= 100 and int(country) <= 150:
                slug = slug + "&areaCode=" + country
            base_url = base_url + slug
            json_data = requests.get(base_url).json()
            print(json_data)
    return json_data