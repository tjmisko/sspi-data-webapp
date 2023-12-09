import requests
import bs4 as bs
from ..resources.utilities import string_to_float, string_to_int
from ... import sspi_raw_api_data
import urllib3
import ssl

def collectOECDIndicator(OECDIndicatorCode, IndicatorCode, **kwargs):
    """
    The CustomHTTPAdapter class and the legacy session are necessary to connect to the OECD SDMX API
    because OECD does not support RFC 5746 secure renegotiation, which is the default for OpenSSL 3

    See Harry Mallon's answer and ahmkara's elaboration on StackOverflow:
    https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled/71646353#71646353
    """
    class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

        def __init__(self, ssl_context=None, **kwargs):
            self.ssl_context = ssl_context
            super().__init__(**kwargs)

        def init_poolmanager(self, connections, maxsize, block=False):
            self.poolmanager = urllib3.poolmanager.PoolManager(
                num_pools=connections, maxsize=maxsize,
                block=block, ssl_context=self.ssl_context)
    
    def get_legacy_session():
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        session = requests.session()
        session.mount('https://', CustomHttpAdapter(ctx))
        return session
        

    SDMX_URL_OECD_METADATA = f"https://stats.oecd.org/RestSDMX/sdmx.ashx/GetKeyFamily/{OECDIndicatorCode}"
    SDMX_URL_OECD = f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/{OECDIndicatorCode}"
    yield "Sending Metadata Request to OECD SDMX API\n"
    metadata_obj = get_legacy_session().get(SDMX_URL_OECD_METADATA)
    metadata = str(metadata_obj.content)
    yield "Metadata Received from OECD SDMX API.  Sending Data Request to OECD SDMX API\n"
    yield "Sending Data Request to OECD SDMX API\n"
    response_obj = get_legacy_session().get(SDMX_URL_OECD)
    observation = str(response_obj.content) 
    yield "Data Received from OECD SDMX API.  Storing Data in SSPI Raw Data\n"
    sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, Source="OECD", Metadata=metadata, **kwargs)
    yield "Data Stored in SSPI Raw Data.  Collection Complete\n"

# ghg (total), ghg (index1990), ghg (ghg cap), co2 (total)

def extractAllSeries(oecd_XML):
    xml_soup = bs.BeautifulSoup(oecd_XML, "lxml")
    series_list = xml_soup.find_all("series")
    return series_list

def filterSeriesList(series_list, filterVAR, OECDIndicatorCode, IndicatorCode):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find("serieskey"), series.find("attributes")
        VAR = series_key.find("value", attrs={"concept": "VAR"}).get("value")
        if VAR != filterVAR:
            continue
        id_info = {
            "CountryCode": series_key.find("value", attrs={"concept": "COU"}).get("value"),
            "VariableCodeOECD": VAR,
            "IndicatorCodeOECD": OECDIndicatorCode,
            "Source": "OECD",
            "IndicatorCode": IndicatorCode,
            "Units": series_attributes.find("value", attrs={"concept": "UNIT"}).get("value"),
            "Pollutant": series_key.find("value", attrs={"concept": "POL"}).get("value"),
        }
        new_documents = [{"Year": obs.find("time").text, "Raw":obs.find("obsvalue").get("value")} for obs in series.find_all("obs")]
        for doc in new_documents:
            doc.update(id_info)
        document_list.extend(new_documents)
    return document_list
        
def filterSeriesListSeniors(series_list, filterIND, OECDIndicatorCode, IndicatorCode):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find("serieskey"), series.find("attributes")
        IND = series_key.find("value", attrs={"concept": "IND"}).get("value")
        if IND != filterIND:
            continue
        id_info = {
            "IndicatorCode": IndicatorCode,
            "CountryCode": series_key.find("value", attrs={"concept": "COU"}).get("value"),
            "Units": series_attributes.find("value", attrs={"concept": "UNIT"}).get("value"),
            "VariableCodeOECD": IND,
            "IndicatorCodeOECD": OECDIndicatorCode,
            "Source": "OECD",
        }
        new_documents = [{"Year": obs.find("time").text, "Raw":obs.find("obsvalue").get("value")} for obs in series.find_all("obs")]
        for doc in new_documents:
            doc.update(id_info)
        document_list.extend(new_documents)
    return document_list
    
def organizeOECDdata(series_list):
    listofdicts = []
    for series in series_list:
        SeriesKeys = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}SeriesKey/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Attributes = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Attributes/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Observation_time = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Obs/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Time")
        Observation_value = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Obs/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}ObsValue")
        relevant_attribute = [True for x in Attributes if x.attrib["value"] == "T_CO2_EQVT"]
        relevant_key = [True for y in SeriesKeys if y.attrib["value"] == "CO2"]
        if relevant_attribute and relevant_key:
            year_lst = [year.text for year in Observation_time]
            obs_lst = [obs.attrib["value"] for obs in Observation_value]
            for value in SeriesKeys:
                if value.attrib["concept"] == "COU":
                    cou = value.attrib["value"]   
                    i = 0
                    while i <= (len(year_lst)- 1):
                        new_observation = {
                            "CountryCode": cou,
                            "IndicatorCode": "GTRANS",
                            "Source": "OECD",
                            "YEAR": string_to_int(year_lst[i]),
                            "RAW": string_to_float(obs_lst[i])
                        }
                        listofdicts.append(new_observation)
                        i += 1
    return listofdicts

def OECD_country_list(series_list):
    country_lst = []
    for series in series_list:
        SeriesKeys = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}SeriesKey/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Attributes = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Attributes/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        relevant_attribute = [True for x in Attributes if x.attrib["value"] == "T_CO2_EQVT"]
        relevant_key = [True for y in SeriesKeys if y.attrib["value"] == "CO2"]
        if relevant_attribute and relevant_key:
            for value in SeriesKeys:
                if value.attrib["concept"] == "COU":
                    cou = value.attrib["value"]
                    country_lst.append(cou)
    print("this is the oecd country list:" + str(country_lst))
    return country_lst
    
        
