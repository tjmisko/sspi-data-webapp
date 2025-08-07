from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata


@dataset_collector("UNSDG_REDLST")
def collect_unsdg_redlst(**kwargs):
     yield from collect_sdg_indicator_data("15.5.1", **kwargs)


@dataset_cleaner("UNSDG_REDLST")
def clean_unsdg_redlst():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_REDLST"})
    source_info = sspi_metadata.get_source_info("UNSDG_REDLST")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_redlst = extract_sdg(raw_data)
    idcode_map = {
        "ER_RSK_LST": "UNSDG_REDLST",
    }
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
    unsdg_redlst = filter_sdg(
        extracted_unsdg_redlst,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_redlst)
    sspi_metadata.record_dataset_range(unsdg_redlst, "UNSDG_REDLST")
    return unsdg_redlst
