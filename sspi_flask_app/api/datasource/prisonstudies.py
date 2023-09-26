import time
import requests
from bs4 import BeautifulSoup
import pycountry

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
    count = 1
    for url_slug in url_slugs:
        print(url_slug)
        COU = get_country_code(url_slug[8:])
        print(COU)
        # response = requests.get(url_base + url_slug)
        time.sleep(1)
        yield f"Collecting data for country {count} of {len(url_slugs)} from {url_base + url_slug}"
        # html = BeautifulSoup(response.text, 'html.parser')
        # table = html.find("table", {"id": "views-aggregator-datatable"})
        # print(table)
        count += 1

def get_country_code(namestring):
    return pycountry.countries.search_fuzzy(namestring)[0].alpha_3