import json
import requests
import time
from ..api import parse_json


def find_indicator(input_tbd):
    # will develop to search for specific indicator values
    json_data = requests.get()


def collect_indicator_data(indicator_code):
    json_data = requests.get('https://api.iea.org/stats/indicator/' + indicator_code + '?').json()
    m_49lst = []
    for observation in json_data:
        m49item = observation['country']
        m_49lst.append(m49item)
    observation_lst = []
    for country in m_49lst:
        base_url = 'https://api.iea.org/stats/indicator/' + indicator_code + '?'
        country_specific_url = base_url + '&countries=' + str(country)
        specific_json_data = requests.get(country_specific_url).json()
        observation_lst.append(specific_json_data)
    return observation_lst

    

        

    