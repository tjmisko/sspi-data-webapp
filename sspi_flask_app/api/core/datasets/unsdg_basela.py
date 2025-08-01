from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("UNSDG_BASELA")
def collect_unsdg_basela(**kwargs):
    yield from collect_sdg_indicator_data("12.4.1", **kwargs)

@dataset_cleaner("UNSDG_BASELA")
def clean_unsdg_basela():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_BASELA"})
    source_info = sspi_metadata.get_source_info("UNSDG_BASELA")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_basela = extract_sdg(raw_data)
    idcode_map = {"SG_HAZ_CMRBASEL": "UNSDG_BASELA"}
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
    unsdg_stkhlm = filter_sdg(
        extracted_unsdg_basela,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_stkhlm)
    return unsdg_stkhlm
