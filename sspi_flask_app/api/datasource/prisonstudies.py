import time
import requests
from bs4 import BeautifulSoup
import pycountry
import pandas as pd
from ..resources.utilities import parse_json, print_json
from ... import sspi_raw_api_data
from datetime import datetime

def collectPrisonStudiesData():
    url_slugs = get_href_list()
    yield from collect_all_pages(url_slugs)

def get_href_list():
    url_for_clist = "https://www.prisonstudies.org/highest-to-lowest/prison-population-total?field_region_taxonomy_tid=All"
    response = requests.get(url_for_clist)
    # root = ET.fromstring(response.text)
    html = BeautifulSoup(response.text, 'html.parser')
    table = html.find("table", {"summary":"Highest to Lowest"})
    list_of_links = table.findChildren("a", recursive=True)
    url_slugs = [link["href"] for link in list_of_links]
    return url_slugs

def collect_all_pages(url_slugs):
    url_base = "https://www.prisonstudies.org"
    count = 0
    failed_matches = []
    print(url_slugs)
    for url_slug in url_slugs:
        query_string = url_slug[9:].replace("-", " ")
        count += 1
        print(url_slug)
        yield f"{url_slug}\n"
        try:
            COU = get_country_code(query_string)
        except LookupError:
            yield f"Error! Could not find country based on query string '{query_string}'\n"
            if query_string in namefix.keys():
                COU = get_country_code(namefix[query_string])
            else:
                failed_matches.append(query_string)
                continue
        yield f"Collecting data for country {count} of {len(url_slugs)} from {url_base + url_slug}\n"
        # The site blocked my IP after only a few requests, so 30 is here to be conservative
        time.sleep(10)
        print(url_slug)
        response = requests.get(url_base + url_slug)
        yield store_webpage_as_raw_data(response, COU)
        

def get_country_code(namestring):
    return pycountry.countries.search_fuzzy(namestring)[0].alpha_3

namefix = {
    "ireland republic": "ireland",
    "united states america": "usa",
    "cyprus republic": "cyprus",
    "democratic republic congo": "cod",
    "myanmar formerly burma": "myanmar",
    "congo republic": "cog",
    "democratic peoples republic north korea": "north korea",
    "republic south korea": "south korea",
    "cote divorie": "ivoire"
}

def store_webpage_as_raw_data(response, COU):
    sspi_raw_api_data.insert_one({
        "collection-info": {
            "IndicatorCode": "PRISON",
            "CountryCode": COU,
            "CollectedAt": datetime.now()
        },
        "observation": response.text
    })
    return f"Scraped webpage for {COU} and inserted HTML data into sspi_raw_api_data\n"        

def scrape_stored_pages_for_data():
    prison_data = parse_json(sspi_raw_api_data.find({"collection-info.IndicatorCode": "PRISON"}))
    for page_entry in prison_data:
        COU = page_entry["collection-info"]["CountryCode"]
        html = BeautifulSoup(page_entry["observation"], 'html.parser')
        # dynamicDataTable = html.find("table", {"id": "views-aggregator-datatable"})
        # yield str(dynamicDataTable)
    return "success!"
 