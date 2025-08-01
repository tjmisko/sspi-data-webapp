from sspi_flask_app.api.datasource.unfao import collect_unfao_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import jq


@dataset_collector("UNFAO_BFPROD")
def collect_unfao_bfprod(**kwargs):
    yield from collect_unfao_data(
        "2910%2C645%2C2610%2C2510%2C511", "2501", "FBS", **kwargs
    )


@dataset_cleaner("UNFAO_BFPROD")
def clean_unfao_bfprod():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNFAO_BFPROD"})
    source_info = sspi_metadata.get_source_info("UNFAO_BFPROD")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    jq_filter = (
        ".[].Raw.data.[] | select( "
        '.Element == "Production") | '
        'select(."Area Code (ISO3)" | length == 3) | '
        'select(."Area Code (ISO3)" | test("^[A-Z]{3}$"))'
    )
    all_observations = jq.compile(jq_filter).input(raw_data).all()
    
    jq_transform = (
        ".[] | {"
        'DatasetCode: "UNFAO_BFPROD", '
        'CountryCode: ."Area Code (ISO3)", '
        "Year: (.Year | tonumber), "
        "Value: ((.Value | tonumber) * 1e6), "  # Convert to kg
        'Unit: "kg"'
        "}"
    )
    cleaned_data = jq.compile(jq_transform).input(all_observations).all()
    
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)