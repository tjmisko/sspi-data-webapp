from flask import Blueprint, jsonify
from flask_login import login_required
from ... import sspi_clean_api_data, sspi_imputed_data, sspi_production_data, sspi_metadata, sspi_static_radar_data, sspi_main_data_v3
from sspi_flask_app.api.resources.utilities import parse_json, country_code_to_name

finalize_bp = Blueprint(
    'finalize_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@finalize_bp.route("/production/finalize")
@login_required
def production_data():
    return jsonify(production_data_by_indicator())

def finalize_sspi_static_radar_data():
    main_data = sspi_main_data_v3.find({})
    indicator_details = sspi_metadata.indicator_details()
    # build country lookup
    country_lookup = {}
    for document in main_data:
        country_code = document["CountryCode"]
        if not country_code in country_lookup.keys():
            country_lookup[country_code] = {"Data": []}
        country_lookup[country_code]["Data"].append(document)
    radar_data = []
    for country_code, data_dict in country_data.items():
        output_dict = {"CountryCode": country_code}
        sspi = SSPI(indicator_details, country_lookup[country_code]["Data"])
        output_dict["labels"] = [c.name for in sspi.categories]
        output_dict["datasets"] = []
        for pillar in sspi.pillars:
            data = [None] * len(sspi.categories)
            output_dict["datasets"].append({
                "label": pillar.name,
                "data": 
                "backgroundColor": '#28a74566',
                "borderColor": '#28a74566',
                "pointBackgroundColor": '#28a74566',
                "pointBorderColor": '#fff',
                "pointHoverBackgroundColor": '#fff',
                "pointHoverBorderColor": '#28a745',
                "fill": True
            })

            # output_dict
    sspi_static_radar_data.insert_many(radar_data)
    return ""

    # sspi_static_radar_data

def production_data_by_indicator():
    """
    Minification is important for production data to minimize response times
    
    IndicatorCode -> IDCode
    CountryCode -> CCode
    CountryName -> CName
    Intermediates -> Intrmdts
    IntermediateCode -> IMCode
    """
    production_documents = []
    return "0"
    # for IndicatorCode in sspi_metadata.indicator_codes():
    #     print(f"Processing {IndicatorCode}")
    #     production_document = {"Endpoint": "/data/indicator/IDCode", "IDCode": IndicatorCode}
    #     query_results = sspi_clean_api_data.find({"IndicatorCode": IndicatorCode}, {"_id": 0})
    #     dataset_dictionary = {}
    #     # Minify the data and group it by CountryCode
    #     for document in query_results:
    #         document["CName"] = country_code_to_name(document["CountryCode"])
    #         if "Intermediates" in document.keys():
    #             document["Intrmdts"] = document["Intermediates"]
    #             del document["Intermediates"]
    #             for intermediate in document["Intrmdts"]:
    #                 intermediate["IMCode"] = intermediate["IntermediateCode"]
    #                 del intermediate["IntermediateCode"]
    #                 del intermediate["IndicatorCode"]
    #                 del intermediate["CountryCode"]
    #                 del intermediate["Description"]
    #                 del intermediate["Year"]
    #                 del intermediate["LowerGoalpost"]
    #                 del intermediate["UpperGoalpost"]
    #                 del intermediate["Unit"]
    #         del document["Unit"]
    #         document["IDCode"] = document["IndicatorCode"]
    #         del document["IndicatorCode"]
    #         document["CCode"] = document["CountryCode"]
    #         del document["CountryCode"]
    #         if not document["CCode"] in dataset_dictionary.keys():
    #             dataset_dictionary[document["CCode"]] = []
    #         dataset_dictionary[document["CCode"]].append(document)
    #         print(document)
    #     return_data = {"labels": [], "datasets": []}
    #     # Sort the data by Year within CountryCode and create the labels array
    #     for country_code, data in dataset_dictionary.items():
    #         dataset_dictionary[country_code] = sorted(data, key=lambda x: x["Year"])
    #         for document in data:
    #             if not document["Year"] in return_data["labels"]:
    #                 return_data["labels"].append(document["Year"])
    #         data_label = f"{country_code_to_name(country_code)} ({country_code})"
    #         return_data["datasets"].append({"label": data_label, "data": dataset_dictionary[country_code], "parsing": {"xAxisKey": "Year", "yAxisKey": "Score"}})
    #     return_data["labels"] = sorted(return_data["labels"])
    #     production_document["data"] = return_data
    #     sspi_production_data.insert_one(production_document)
    #     del production_document["_id"]
    #     production_documents.append(production_document)
    # return production_documents
