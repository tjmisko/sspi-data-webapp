from flask import Blueprint, jsonify
from flask_login import login_required
from ... import sspi_clean_api_data, sspi_imputed_data, sspi_metadata, sspi_static_radar_data, sspi_main_data_v3, sspi_dynamic_line_data
from sspi_flask_app.api.resources.utilities import parse_json, country_code_to_name, colormap
from sspi_flask_app.models.sspi import SSPI

finalize_bp = Blueprint(
    'finalize_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@finalize_bp.route("/production/finalize")
@login_required
def finalize_all_production_data():
    finalize_sspi_static_radar_data()
    return "Successfully finalized all production data!"


@finalize_bp.route("/production/finalize/dynamic/line")
@login_required
def finalize_sspi_dynamic_line_data():
    """
    Prepare the data for a Chart.js line plot
    """
    sspi_dynamic_line_data.delete_many({})
    for IndicatorCode in sspi_metadata.indicator_codes():
        detail = sspi_metadata.get_detail(IndicatorCode)["Metadata"]
        indicator_dict = {}
        data = sspi_clean_api_data.find(
            {"IndicatorCode": IndicatorCode},
            {"_id": 0}
        )
        for observation in data:
            CountryCode = observation["CountryCode"]
            if CountryCode not in indicator_dict.keys():
                indicator_dict[CountryCode] = []
            indicator_dict[CountryCode].append(observation)
        for CountryCode, document in indicator_dict.items():
            document = sorted(document, key=lambda x: x["Year"])
            document = {
                "CCode": CountryCode,
                "CName": country_code_to_name(CountryCode),
                "ICode": IndicatorCode,
                "IName": detail["Indicator"],
                "CatCode": detail["CategoryCode"],
                "CatName": detail["Category"],
                "PilCode": detail["PillarCode"],
                "PilName": detail["Pillar"],
                "CGroup": sspi_metadata.get_country_groups(CountryCode),
                "fixed": False,
                "label": f"{country_code_to_name(CountryCode)} ({CountryCode})",
                "years": [d["Year"] for d in document],
                "scores": [round(d["Score"], 3) for d in document],
                "data": [round(d["Score"], 3) for d in document],
                "values": [round(d["Value"], 3) for d in document],
            }
            sspi_dynamic_line_data.insert_one(document)
    return jsonify(sspi_dynamic_line_data.find({}, {"_id": 0}))


@finalize_bp.route("/production/finalize/static/radar")
@login_required
def finalize_sspi_static_radar_data():
    sspi_static_radar_data.delete_many({})

    def make_country_lookup(main_data):
        country_lookup = {}
        for document in main_data:
            country_code = document["CountryCode"]
            if country_code not in country_lookup.keys():
                country_lookup[country_code] = {"Data": []}
            country_lookup[country_code]["Data"].append(document)
        return country_lookup

    main_data = sspi_main_data_v3.find({}, {"_id": 0})
    indicator_details = sspi_metadata.indicator_details()
    # build country lookup
    country_lookup = make_country_lookup(main_data)
    radar_data = []
    for country_code, data_dict in country_lookup.items():
        output_dict = {
            "CCode": country_code,
            "Year": 2018
        }
        sspi = SSPI(indicator_details, country_lookup[country_code]["Data"])
        output_dict["labels"] = [c.name for c in sspi.categories]
        output_dict["datasets"] = []
        category_start_index = 0
        for pillar in sspi.pillars:
            data = [None] * len(sspi.categories)
            for i, category in enumerate(pillar.categories):
                data[category_start_index + i] = round(category.score(), 3)
            category_start_index += len(pillar.categories)
            pillar_color = colormap(pillar.code, alpha="66")
            output_dict["datasets"].append({
                "label": pillar.name,
                "data": data,
                "backgroundColor": pillar_color,
                "borderColor": pillar_color,
                "pointBackgroundColor": pillar_color,
                "pointBorderColor": '#fff',
                "pointHoverBackgroundColor": '#fff',
                "pointHoverBorderColor": pillar_color,
                "fill": True
            })
        radar_data.append(output_dict)
    sspi_static_radar_data.insert_many(radar_data)
    return "Successfully finalized radar data!"

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
    return "0"
