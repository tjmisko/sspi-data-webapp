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

def filterSeriesListILO(series_list, filterVAR, ILOIndicatorCode, IndicatorCode):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find("generic:serieskey"), series.find("generic:attributes")
        VAR = series_key.find("generic:value", attrs={"concept": "VAR"}).get("value")
        if VAR != filterVAR:
            continue
        id_info = {
            "CountryCode": series_key.find("generic:value", attrs={"concept": ""}).get("value"),
            "VariableCodeOECD": VAR,
            "IndicatorCodeOECD": ILOIndicatorCode,
            "Source": "ILO",
            "IndicatorCode": IndicatorCode,
            "Unit": series_attributes.find("value", attrs={"concept": "UNIT"}).get("value"),
            "Pollutant": series_key.find("value", attrs={"concept": "POL"}).get("value"),
        }
        new_documents = [{"Year": obs.find("time").text, "Value":obs.find("obsvalue").get("value")} for obs in series.find_all("obs")]
        for doc in new_documents:
            doc.update(id_info)
        document_list.extend(new_documents)
    return document_list