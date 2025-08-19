from sspi_flask_app.api.datasource.wid import collect_wid_data, fetch_wid_raw_data, filter_wid_csv
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50")
def collect_nincsh_posttax_equalsplit_p0p50(**kwargs):
    yield from collect_wid_data(**kwargs)


@dataset_cleaner("WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50")
def clean_nincsh_posttax_equalsplit_p0p50():
    """
    Distribution of post-tax national income shares for the bottom 50% of earners for equal-split adults
    """
    sspi_clean_api_data.delete_many({"DatasetCode": "WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50"})
    sspi_67 = sspi_metadata.country_group("SSPI67")
    cleaned_data = []
    year_range = list(range(2000, 2025))
    for cou in sspi_67:
        raw, meta = fetch_wid_raw_data(cou)
        output_list = filter_wid_csv("WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50", raw["Raw"], cou, "p0p50", "sdiincj992", year_range, metadata_csv_string=meta["Raw"])
        cleaned_data.extend(output_list)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50")
    return parse_json(cleaned_data)
