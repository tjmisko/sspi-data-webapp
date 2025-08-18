from sspi_flask_app.api.datasource.iea import collect_iea_data, clean_iea_data_altnrg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import pandas as pd
import json


@dataset_collector("IEA_HYDROP")
def collect_iea_hydrop(**kwargs):
    yield from collect_iea_data("TESbySource", **kwargs)


@dataset_cleaner("IEA_HYDROP")
def clean_iea_hydrop():
    sspi_clean_api_data.delete_many({"DatasetCode": "IEA_HYDROP"})
    source_info = sspi_metadata.get_source_info("IEA_HYDROP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    intermediate_data = pd.DataFrame(clean_iea_data_altnrg(raw_data, "IEA_HYDROP"))
    intermediate_data.drop(
        intermediate_data[
            intermediate_data["CountryCode"].map(lambda s: len(s) != 3)
        ].index.tolist(),
        inplace=True,
    )
    
    # Filter only for HYDRO (hydroelectric) data
    intermediate_data = intermediate_data[intermediate_data["IntermediateCode"] == "HYDRO"]
    intermediate_data["IntermediateCode"] = "HYDROP"
    intermediate_data.astype({"Year": "int", "Value": "float"})
    
    # Assign DatasetCode to all records
    intermediate_data["DatasetCode"] = "IEA_HYDROP"
    
    intermediate_document_list = json.loads(
        str(intermediate_data.to_json(orient="records")),
        parse_int=int,
        parse_float=float,
    )
    
    sspi_clean_api_data.insert_many(intermediate_document_list)
    sspi_metadata.record_dataset_range(intermediate_document_list, "IEA_HYDROP")
    return parse_json(intermediate_document_list)