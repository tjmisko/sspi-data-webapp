###########################################################
# Documentation: datasets/who/who_fampln/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.who import collect_who_data 
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import jq


@dataset_collector("WHO_FAMPLN")
def collect_who_fampln(**kwargs):
    yield from collect_who_data("SDGFPALL", **kwargs)


@dataset_cleaner("WHO_FAMPLN")
def clean_who_fampln():
    sspi_clean_api_data.delete_many({"DatasetCode": "WHO_FAMPLN"})
    source_info = sspi_metadata.get_source_info("WHO_FAMPLN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)[0]["Raw"]
    # Slice out the relevant data and identifiers (in Dim array)
    return parse_json(raw_data)
    first_slice = '.[] | {DatasetCode: "WHO_FAMPLN", Value: .value.numeric, Dim }'
    first_slice_filter = jq.compile(first_slice)
    dim_list = first_slice_filter.input(raw_data).all()

    # Reduce/Flatten the Dim array
    map_reduce = (
        '.[] |  reduce .Dim[] as $d (.; .[$d.category] = $d.code) | '
        'select(.WHO == "NUTSTUNTINGPREV")'
    )
    map_reduce_filter = jq.compile(map_reduce)
    reduced_list = map_reduce_filter.input(dim_list).all()
    # Remap the keys to the correct names
    rename_keys = (
        '.[] | { DatasetCode, CountryCode: .COUNTRY,'
        'Year: .YEAR, Value, Unit: "Percentage" }'
    )
    rename_keys_filter = jq.compile(rename_keys)
    cleaned_data = rename_keys_filter.input(reduced_list).all()
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WHO_FAMPLN")
    return parse_json(cleaned_data)
