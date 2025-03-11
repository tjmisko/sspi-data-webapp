import requests
from sspi_flask_app.models.database import sspi_raw_api_data
import bs4 as bs
from pycountry import countries
from ..resources.utilities import get_country_code, country_code_to_code

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

def cleanIEAData_altnrg(RawData, IndName):
    """
    Takes in list of collected raw data and our 6 letter indicator code 
    and returns a list of dictionaries with only relevant data from wanted countries
    """
    clean_data_list = []
    for entry in RawData:
        country = entry["Raw"]["country"]
        if len(country) > 3:
            continue
        country_code = countries.get(alpha_3 = country).alpha_3
        value = entry["Raw"]['value']
        if not country_code:
            continue
        if not value:
            continue
        clean_obs = {
            "CountryCode": country_code,
            "IndicatorCode": IndName,
            "Year": entry["Raw"]["year"],
            "Value": entry["Raw"]["value"],
            "Unit": entry['Raw']['units'],
            "IntermediateCode": entry['Raw']['product']
        }
        clean_data_list.append(clean_obs)
    return clean_data_list

def clean_IEA_data_GTRANS(raw_data, indicator_code, description):
    clean_data_list = []
    for obs in raw_data:
        country = obs["Raw"]["country"]
        if len(country) > 3:
            continue
        if countries.get(alpha_3 = country) == None:
            continue
        country_code = country_code_to_code(country)
        value = obs["Raw"]['value']
        intermediate_code = obs["IntermediateCode"]
        series_label = obs["Raw"]["seriesLabel"]
        if series_label != "Transport Sector":
            continue
        if not country_code:
            continue
        if not value:
            continue
        print(obs)
        clean_obs = {
            "CountryCode": country_code,
            "IndicatorCode": indicator_code,
            "Year": obs["Raw"]["year"],
            "Value": (obs["Raw"]["value"]) * 1000, # Metric tonnes to thousands of kilograms
            "Unit": "Kilograms of CO2",
            "Description": description,
            "IntermediateCode": intermediate_code
        }
        clean_data_list.append(clean_obs)
    return clean_data_list



