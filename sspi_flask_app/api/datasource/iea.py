import requests
from sspi_flask_app.models.database import sspi_raw_api_data
import pycountry

def collect_iea_data(iea_indicator_code, **kwargs):
    url = f"https://api.iea.org/stats/indicator/{iea_indicator_code}"
    raw_data = requests.get(url).json()
    source_info = {
        "OrganizationName": "International Energy Organization",
        "OrganizationCode": "IEA",
        "OrganizationSeriesCode": iea_indicator_code,
        "BaseURL": url,
        "URL": url
    }
    count = sspi_raw_api_data.raw_insert_many(raw_data, source_info, **kwargs)
    yield f"Successfully inserted {count} observations of IEA Indicator {iea_indicator_code}"

def filter_series_list_iea(series_list, filterVAR, IndicatorCode):
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

def clean_iea_data_altnrg(RawData, IndName):
    """
    Takes in list of collected raw data and our 6 letter indicator code 
    and returns a list of dictionaries with only relevant data from wanted countries
    """
    clean_data_list = []
    for entry in RawData:
        iso3 = entry["Raw"]["country"]
        country_data = pycountry.countries.get(alpha_3=iso3)
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
            "IntermediateCode": entry['Raw']['product']
        }
        clean_data_list.append(clean_obs)
    return clean_data_list


def clean_IEA_data_GTRANS(raw_data, indicator_code, description):
    def convert_to_kg(value):
        return value * 10**9
    clean_data_list = []
    for obs in raw_data:
        iso3 = obs["Raw"]["country"]
        country_data = pycountry.countries.get(alpha_3=iso3)
        value = obs["Raw"]['value']
        intermediate_code = obs["IntermediateCode"]
        series_label = obs["Raw"]["seriesLabel"]
        if series_label != "Transport Sector":
            continue
        if not country_data:
            continue
        if not value and (type(value) is not float or type(value) is not int):
            continue
        clean_obs = {
            "CountryCode": iso3,
            "IndicatorCode": indicator_code,
            "Year": obs["Raw"]["year"],
            "Value": convert_to_kg(obs["Raw"]["value"]),
            "Unit": "Tonnes C02 per inhabitant",
            "Description": description,
            "IntermediateCode": intermediate_code
        }
        clean_data_list.append(clean_obs)
    return clean_data_list
