from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    filter_incomplete_data,
    score_single_indicator
)
from sspi_flask_app.api.datasource.who import (
    cleanWHOdata
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_fampln
)
from flask import current_app as app
import jq


@compute_bp.route("/ATBRTH")
@login_required
def compute_atbrth():
    app.logger.info("Running /api/v1/compute/ATBRTH")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ATBRTH"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ATBRTH")
    description = """
    The proportion of births attended by trained and/or skilled
    health personnel
    """
    cleaned = cleanWHOdata(raw_data, "ATBRTH", "Percent", description)
    scored = score_single_indicator(cleaned, "ATBRTH")
    filtered_list, incomplete_data = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/DPTCOV")
@login_required
def compute_dptcov():
    app.logger.info("Running /api/v1/compute/DPTCOV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DPTCOV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("DPTCOV")
    description = "DTP3 immunization coverage among one-year-olds (%)"
    cleaned = cleanWHOdata(raw_data, "DPTCOV", "Percent", description)
    scored = score_single_indicator(cleaned, "DPTCOV")
    filtered_list, incomplete_data = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/PHYSPC")
@login_required
def compute_physpc():
    app.logger.info("Running /api/v1/compute/PHYSPC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PHYSPC"})
    raw_data = sspi_raw_api_data.fetch_raw_data("PHYSPC")
    unit = "Doctors/10000"
    description = """
    Number of medical doctors (physicians), both generalists and specialists,
    expressed per 10,000 people.
    """
    cleaned = cleanWHOdata(raw_data, "PHYSPC", unit, description)
    scored = score_single_indicator(cleaned, "PHYSPC")
    filtered_list, incomplete_data = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/FAMPLN")
@login_required
def compute_fampln():
    app.logger.info("Running /api/v1/compute/FAMPLN")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FAMPLN"})
    raw_data = sspi_raw_api_data.fetch_raw_data("FAMPLN")
    inter = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    final = flatten_nested_dictionary_fampln(inter)
    computed_list = score_single_indicator(final, "FAMPLN")
    filtered_list, incomplete_data = filter_incomplete_data(computed_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(len(incomplete_data))
    return parse_json(filtered_list)


@compute_bp.route("/CSTUNT", methods=['GET'])
@login_required
def compute_cstunt():
    app.logger.info("Running /api/v1/compute/CSTUNT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CSTUNT"})
    raw_data = sspi_raw_api_data.fetch_raw_data("CSTUNT")[0]["Raw"]["fact"]
    # Slice out the relevant data and identifiers (in Dim array)
    first_slice = '.[] | {IndicatorCode: "CSTUNT", Value: .value.numeric, Dim }'
    first_slice_filter = jq.compile(first_slice)
    dim_list = first_slice_filter.input(raw_data).all()
    # Reduce/Flatten the Dim array
    map_reduce = '.[] |  reduce .Dim[] as $d (.; .[$d.category] = $d.code)'
    map_reduce_filter = jq.compile(map_reduce)
    reduced_list = map_reduce_filter.input(dim_list).all()
    # Remap the keys to the correct names
    rename_keys = (
        '.[] | { IndicatorCode, CountryCode: .COUNTRY,'
        'Year: .YEAR, Value, Unit: "Percentage" }'
    )
    rename_keys_filter = jq.compile(rename_keys)
    value_list = rename_keys_filter.input(reduced_list).all()
    # Score the indicator data
    scored_list = score_single_indicator(value_list, "CSTUNT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
