from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy
from io import BytesIO
from sspi_flask_app.models.database import sspi_raw_api_data


def collectFSIdata(IndicatorCode, **kwargs):
    url = "https://fragilestatesindex.org/excel/"
    # need to specify user agent otherwise requests are blocked
    header = {"User-Agent":
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"} 
    response = requests.get(url, headers = header)
    if response.status_code != 200:
        return "Add header with user agent so request is not blocked"
    soup = BeautifulSoup(response.text, "html.parser")
    excel_a_tags = soup.find_all('a')
    links = []
    for a_tag in excel_a_tags:
        link = a_tag.get("href")
        links.append(link)
    for link in links:
        excel = requests.get(link, headers = header).content
        excel_readable = BytesIO(excel)
        df = pd.read_excel(excel_readable, engine = "openpyxl")
        print(df)
        break
    return "hi"
