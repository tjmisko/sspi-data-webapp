import json
from sspi_flask_app.api.datasource.ilo import collect_ilo_data, extract_ilo, filter_ilo
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("ILO_EMPLOY_TO_POP")
def collect_ilo_employ_to_pop(**kwargs):
    yield from collect_ilo_data(
        "DF_EMP_DWAP_SEX_AGE_RT",
        QueryParams=".A..SEX_T.AGE_YTHADULT_Y15-64",
        URLParams=["startPeriod=2000"],
        **kwargs
    )


@dataset_cleaner("ILO_EMPLOY_TO_POP")
def clean_ilo_employ_to_pop():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_EMPLOY_TO_POP"})
    source_info = sspi_metadata.get_source_info("ILO_EMPLOY_TO_POP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_ilo(raw_data)
    obs_list = filter_ilo(extracted_data, "ILO_EMPLOY_TO_POP", SEX="SEX_T", AGE="AGE_YTHADULT_Y15-64")
    sspi_clean_api_data.insert_many(obs_list)
    sspi_metadata.record_dataset_range(obs_list, "ILO_EMPLOY_TO_POP")
    return parse_json(obs_list)
