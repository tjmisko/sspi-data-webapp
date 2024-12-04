import time
import requests
from bs4 import BeautifulSoup
import pycountry
import pandas as pd
from ..resources.utilities import parse_json
from sspi_flask_app.models.database import sspi_raw_api_data
from datetime import datetime
import base64

def collectPrisonStudiesData(**kwargs):
    url_slugs = get_href_list()
    yield from collect_all_pages(url_slugs, **kwargs)

def get_href_list():
    '''
    Collects unique ends of URLs for each country, each of which hosts time series data (along with other characteristics)
    '''
    url_for_clist = "https://www.prisonstudies.org/highest-to-lowest/prison-population-total?field_region_taxonomy_tid=All"
    response = requests.get(url_for_clist)
    # root = ET.fromstring(response.text)
    html = BeautifulSoup(response.text, 'html.parser')
    table = html.find("table", {"summary":"Highest to Lowest"})
    list_of_links = table.findChildren("a", recursive=True)
    url_slugs = [link["href"] for link in list_of_links]
    return url_slugs

def collect_all_pages(url_slugs, **kwargs):
    url_base = "https://www.prisonstudies.org"
    count = 0
    failed_matches = []
    webpages = []
    print(url_slugs)
    for url_slug in url_slugs:
        query_string = url_slug[9:].replace("-", " ")
        count += 1
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
        response = requests.get(url_base + url_slug)
        # special case of UK being split into three --> scotland, northern ireland, england + wales
        if COU == "GBR":
            COU = COU + url_slug.split("-")[-1]
        webpages.append({COU: response.content})
    print(failed_matches)
    return store_webpages_as_raw_data(webpages, **kwargs)
        # yield store_webpage_as_raw_data(response, COU, **kwargs)
        

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
    "cote divorie": "ivoire",
    "united kingdom england wales": "united kingdom",
    "united kingdom scotland": "united kingdom",
    "united kingdom northern ireland": "united kingdom",
    "bosnia and herzegovina federation": "bosnia and heregovina",
    "kosovokosova": "kosovo"
}

def store_webpages_as_raw_data(webpage_list, **kwargs):
    data_list = []
    count = 0
    for webpage in webpage_list:
        country_code = list(webpage.keys())[0]
        obs = {"IndicatorCode": "INCARC",
         "CountryCode": country_code,
         "Raw": webpage[country_code],
         "ColllectedAt": datetime.now()}
        data_list.append(obs)
        count += 1
        # yield f"Scraped webpage for {country} and inserted HTML data into sspi_raw_api_data\n"
    sspi_raw_api_data.raw_insert_many(data_list, "INCARC", **kwargs)
    return f"All {count} countries' data inserted into raw database"     

def scrape_stored_pages_for_data():
    prison_data = sspi_raw_api_data.find({"IndicatorCode": "INCARC"})
    final_data = []
    gbr_data = []
    missing_countries = []
    for entry in prison_data:
        country = entry["Raw"]["CountryCode"]
        data = entry["Raw"]["Raw"]["$binary"]["base64"]
        web_page = base64.b64decode(data).decode('utf-8')
        table = BeautifulSoup(web_page, 'html.parser').find(
            "table", attrs = {"id": "views-aggregator-datatable", "summary": "Prison population rate"})
        if table is None: 
            print(f"{country} does not have relevant table")
            missing_countries.append(country)
            continue
        # iterate through rows of html table
        table_rows = table.find_all('tr')
        prison_data = []
        for tr in table_rows:
            # row data
            td = tr.find_all("td")
            row = [tr.text.strip() for tr in td if tr.text.strip()]
            if row:
                prison_data.append(row)
        df = pd.DataFrame(prison_data, columns=["Year", "Prison Population Total", "Prison Population Rate"])
        df["Prison Population Total"] = df["Prison Population Total"].replace(",", "", regex = True)
        df["Prison Population Total"] = df["Prison Population Total"].replace("c ", "", regex = True)
        df["Prison Population Rate"] = df["Prison Population Rate"].replace("c ", "", regex = True)
        if "GBR" in country:
            df.apply(lambda row: gbr_data.append(
                {"IndicatorCode": "INCARC",
                "Value": int(row["Prison Population Total"]),
                "Year": int(row["Year"]),
                "CountryCode": country,
                "Unit": "People per 100,000",
                "Description": "Prison population rate per 100,000 of the national population."}), axis = 1)
        else:
            df.apply(lambda row: final_data.append(
                {"IndicatorCode": "INCARC",
                "Value": int(row["Prison Population Total"]),
                "Year": int(row["Year"]),
                "CountryCode": country,
                "Unit": "People per 100,000",
                "Description": "Prison population rate per 100,000 of the national population."}), axis = 1)
    # combine uk values
    gbr_obs = {}
    for obs in gbr_data:
        year = obs["Year"]
        if year not in gbr_obs:
            gbr_obs[year] = []
        gbr_obs[year].append(obs["Value"])
    for year in gbr_obs:
        year_sum = sum(gbr_obs[year])
        obs = {"IndicatorCode": "INCARC",
               "Value": year_sum,
                "Year": year,
                "CountryCode": "GBR",
                "Unit": "People per 100,000",
                "Description": "Prison population rate per 100,000 of the national population."}
        final_data.append(obs)
    return final_data, missing_countries