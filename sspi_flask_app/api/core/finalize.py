from flask import flash, redirect, url_for
from flask_login import login_required
from ..api import api_bp
from ... import sspi_clean_api_data, sspi_imputed_data, sspi_production_data, sspi_metadata
import pycountry
from sspi_flask_app.api.resources.utilities import parse_json

@api_bp.route("/finalize/<indicator_code>")
@login_required
def production_data_by_indicator():
    for IndicatorCode in sspi_metadata.indicator_codes():
        production_document = {"route": "/data/indicator/IndicatorCode", "IndicatorCode": IndicatorCode}
        query_results = sspi_clean_api_data.find( {"IndicatorCode": IndicatorCode})
        dataset_dictionary = {}
        for document in query_results:
            try:
                document["CountryName"] = pycountry.countries.get(alpha_3=document["CountryCode"]).name
            except AttributeError:
                document["CountryName"] = document["CountryCode"]
            if not document["CountryCode"] in dataset_dictionary.keys():
                dataset_dictionary[document["CountryCode"]] = []
            dataset_dictionary[document["CountryCode"]].append(document)
        return_data = {"labels": [], "datasets": []}
        for country_code, data in dataset_dictionary.items():
            dataset_dictionary[country_code] = sorted(data, key=lambda x: x["Year"])
            for document in data:
                if not document["Year"] in return_data["labels"]:
                    return_data["labels"].append(document["Year"])
            data_label = f"({countrycode})"
            return_data["datasets"].append({"label": country_code, "data": dataset_dictionary[country_code], "parsing": {"xAxisKey": "Year", "yAxisKey": "Value"}})
        return_data["labels"] = sorted(return_data["labels"])
        sspi_production_data.insert_one

    return jsonify(return_data)
