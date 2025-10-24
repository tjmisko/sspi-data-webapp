from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("UNSDG_LABRTS")
def collect_unsdg_labrts(**kwargs):
    yield from collect_sdg_indicator_data("8.8.2", **kwargs)

@dataset_cleaner("UNSDG_LABRTS")
def clean_unsdg_labrts():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_LABRTS"})
    source_info = sspi_metadata.get_source_info("UNSDG_LABRTS")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_labrts = extract_sdg(raw_data)
    idcode_map = {"SL_LBR_NTLCPL": "UNSDG_LABRTS"}
    rename_map = {"units": "Unit", "seriesDescription": "Description"}
    drop_list = [
        "goal",
        "indicator",
        "series",
        "seriesCount",
        "target",
        "geoAreaCode",
        "geoAreaName",
    ]
    labrts_stkhlm = filter_sdg(
        extracted_labrts,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(labrts_stkhlm)
    sspi_metadata.record_dataset_range(labrts_stkhlm, "UNSDG_LABRTS")
    return labrts_stkhlm
