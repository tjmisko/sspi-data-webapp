def collectAvailableGeoAreas(indicator_code):
    json_data = requests.get("https://unstats.un.org/sdgapi/v1/sdg/Indicator/" + indicator_code + "/GeoAreas")
    m49_list = []
    for observation in json_data:
        m49_list.append(observation["geoAreaCode"])
    return m49_list

def collectSDGIndicatorData(indicator_code):
    base_url = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/Data?indicator=" + indicator_code + "&timeperiod=1980&timePeriod=2023"
    m49_list = collectAvailableGeoAreas(indicator_code)
    for country in m49_list:
        slug = "&areaCode=" + country
        base_url = base_url + slug
    json_data = requests.get(base_url)
    return len(json_data)