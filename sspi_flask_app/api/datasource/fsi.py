from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy
from io import BytesIO
import re
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.resources.utilities import get_country_code, parse_json


def collect_fsi_data(**kwargs):
    base_url = "https://fragilestatesindex.org/excel/"
    # need to specify user agent otherwise requests are blocked
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"} 
    response = requests.get(base_url, headers = header)
    if response.status_code != 200:
        return "Add header with user agent so request is not blocked"
    soup = BeautifulSoup(base_url, "html.parser")
    excel_a_tags = soup.find_all('a')
    links = {}
    for a_tag in excel_a_tags:
        link = a_tag.get("href")
        if link.find("xlsx") == -1:
            continue
        # multiple links per year for some reason so only want one
        year = re.findall(r'[0-9]{4}', string = link)[0]
        if year not in links.keys():
            links[year] = link
    for year in links.keys():
        data_url = links[year]
        excel = requests.get(data_url, headers = header)
        source_info = {
            "OrganizationName": "Fragile States Index",
            "OrganizationCode": "FSI",
            "QueryCode": "FSI",
            "BaseURL": base_url,
            "URL": data_url
        }
        yield "Collection complete for FSI Data"
        excel_readable = BytesIO(excel.content)
        df = pd.read_excel(excel_readable)
        obs = len(df.index)
        json = df.to_dict(orient = "records")
        sspi_raw_api_data.raw_insert_one(json, source_info, **kwargs)
        yield f"Insered {obs} observations for FSI for {year} into raw database\n"


def clean_fsi_data(raw_data, IndicatorCode, unit, description):
    clean_list = []
    for obs in raw_data:
        data = obs["Raw"]["json"]
        full_df = pd.DataFrame(data)
        filtered = full_df.loc[:, ["Country", "Year", "C1: Security Apparatus"]].rename(
            columns = {"C1: Security Apparatus": "Value"})
        filtered["IndicatorCode"] = IndicatorCode
        filtered["CountryCode"] = filtered["Country"].map(lambda country_name: get_country_code(country_name))
        filtered = filtered.drop(columns = "Country")
        filtered["Unit"] = unit
        filtered["Description"] = description
        # some years are reported as datetime object
        if isinstance(filtered["Year"][0], dict):
            filtered["Year"] = filtered["Year"].map(lambda entry: entry["$date"].split("-")[0]).astype(int)
        # filtered["Value"] = filtered["Value"].astype(float)
        # print(type(filtered["Year"][0]))
        clean_list.extend(filtered.to_dict(orient = "records"))
    return clean_list
