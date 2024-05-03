import requests
from ... import sspi_raw_api_data
import bs4 as bs

def collectILOData(ILOIndicatorCode, IndicatorCode, QueryParams="....", **kwargs):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get(f"https://www.ilo.org/sdmx/rest/data/ILO,{ILOIndicatorCode}/{QueryParams}")
    print(str(response_obj.content))
    observation = str(response_obj.content)
    yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
    yield f"Inserted {count} observations into the database."

def extractAllSeriesILO(ilo_sdmxml):
    soup = bs.BeautifulSoup(ilo_sdmxml, 'lxml')
    series = soup.find_all('generic:series')
    return series

def filterSeriesListlfpart(series_list):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find("generic:serieskey"), series.find("generic:attributes")
        VAR = series_key.find("generic:value", attrs={"id": "MEASURE"}).get("value")
        sex = series_key.find("generic:value", attrs={"id":"SEX"}).get("value")
        if VAR != "EAP_DWAP_RT" or sex !="SEX_T":
            continue
        doc = {
            "CountryCode": series_key.find("generic:value", attrs={"id": "REF_AREA"}).get("value"),
            "IndicatorCode": "LFPART",
            "Unit": series_attributes.find("generic:value", attrs={"id": "UNIT_MEASURE"}).get("value"),
            "Year": series.find("generic:obs").find("generic:obsdimension", attrs={"id": "TIME_PERIOD"}).get("value"),
            "Value": series.find("generic:obs").find("generic:obsvalue").get("value")
        }
        document_list.append(doc)
    return document_list