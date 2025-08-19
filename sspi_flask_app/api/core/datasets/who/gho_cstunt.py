from sspi_flask_app.api.datasource.who import collect_gho_cstunt_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import jq


@dataset_collector("GHO_CSTUNT")
def collect_gho_cstunt(**kwargs):
    yield from collect_gho_cstunt_data(**kwargs)


@dataset_cleaner("GHO_CSTUNT")
def clean_gho_cstunt():
    sspi_clean_api_data.delete_many({"DatasetCode": "GHO_CSTUNT"})
    source_info = sspi_metadata.get_source_info("GHO_CSTUNT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)[0]["Raw"]["fact"]
    # Slice out the relevant data and identifiers (in Dim array)
    first_slice = '.[] | {DatasetCode: "GHO_CSTUNT", Value: .value.numeric, Dim }'
    first_slice_filter = jq.compile(first_slice)
    dim_list = first_slice_filter.input(raw_data).all()
    # Reduce/Flatten the Dim array
    map_reduce = (
        '.[] |  reduce .Dim[] as $d (.; .[$d.category] = $d.code) | '
        'select(.GHO == "NUTSTUNTINGPREV")'
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
    sspi_metadata.record_dataset_range(cleaned_data, "GHO_CSTUNT")
    return parse_json(cleaned_data)