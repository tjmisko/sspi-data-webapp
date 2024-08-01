import requests
from ... import sspi_raw_api_data
import bs4 as bs
from pycountry import countries

def collectIEAData(IEAIndicatorCode, IndicatorCode, **kwargs):
    raw_data = requests.get(f"https://api.iea.org/stats/indicator/{IEAIndicatorCode}").json()
    count = sspi_raw_api_data.raw_insert_many(raw_data, IndicatorCode, **kwargs)
    yield f"Successfully inserted {count} observations into the database"

def filterSeriesListiea(series_list, filterVAR, IndicatorCode):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find("serieskey"), series.find("attributes")
        VAR = series_key.find("value", attrs={"concept": "VAR"}).get("value")
        if VAR != filterVAR:
            continue
        id_info = {
            "CountryCode": series_key.find("value", attrs={"concept": "COU"}).get("value"),
            "VariableCodeIEA": VAR,
            "Source": "IEA",
            "IndicatorCode": IndicatorCode,
            "Unit": series_attributes.find("value", attrs={"concept": "UNIT"}).get("value"),
            "Pollutant": series_key.find("value", attrs={"concept": "POL"}).get("value"),
        }
        new_documents = [{"Year": obs.find("time").text, "Value":obs.find("obsvalue").get("value")} for obs in series.find_all("obs")]
        for doc in new_documents:
            doc.update(id_info)
        document_list.extend(new_documents)
    return document_list

def cleanIEAData_altnrg(RawData, IndName, CodeMap):
    """
    Takes in list of collected raw data and our 6 letter indicator code 
    and returns a list of dictionaries with only relevant data from wanted countries
    """
    clean_data_list = []
    for entry in RawData:
        iso3 = entry["Raw"]["country"]
        country_data = countries.get(alpha_3=iso3)
        value = entry["Raw"]['value']
        if not country_data:
            continue
        if not value:
            continue
        clean_obs = {
            "CountryCode": iso3,
            "IndicatorCode": IndName,
            "Year": entry["Raw"]["year"],
            "Value": entry["Raw"]["value"],
            "Unit": entry['Raw']['units'],
            "IntermediateCode": CodeMap[entry['Raw']['product']],
            "Description": "Percentage of total final energy supply from renewable sources (hydroelectric, geothermal, solar, wind, biofuels) minus half the percentage of total final energy supply from biofuel sources, penalizing countries for unsustainable overreliance on biofuels"
        }
        clean_data_list.append(clean_obs)
    return clean_data_list

def filter_IEA_cleaned(data_dict_list, intermediate_code_list):
    filtered = []
    for observation in data_dict_list:
        if observation["IntermediateCode"] in intermediate_code_list:
            filtered.append(observation)
        else:
            continue
    return filtered
