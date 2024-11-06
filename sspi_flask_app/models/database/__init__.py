from flask_pymongo import MongoClient

from sspi_flask_app.models.database import (
    mongo_wrapper,
    sspi_clean_api_data,
    sspi_country_characteristics,
    sspi_main_data_v3,
    sspi_metadata,
    sspi_partial_api_data,
    sspi_production_data,
    sspi_raw_api_data,
    sspi_outcome_data
)

client = MongoClient('localhost', 27017)
sspidb = client.flask_db

sspi_metadata = sspi_metadata.SSPIMetadata(
    sspidb.sspi_metadata
)
sspi_main_data_v3 = sspi_main_data_v3.SSPIMainDataV3(
    sspidb.sspi_main_data_v3
)
sspi_raw_api_data = sspi_raw_api_data.SSPIRawAPIData(
    sspidb.sspi_raw_api_data
)
sspi_country_characteristics = sspi_country_characteristics.SSPICountryCharacteristics(
    sspidb.sspi_country_characteristics
)
sspi_outcome_data = sspi_outcome_data.SSPIOutcomeData(
    sspidb.sspi_outcome_data
)
sspi_bulk_data = mongo_wrapper.MongoWrapper(
    sspidb.sspi_bulk_data
)
sspi_clean_api_data = sspi_clean_api_data.SSPICleanAPIData(
    sspidb.sspi_clean_api_data
)
sspi_partial_api_data = sspi_partial_api_data.SSPIPartialAPIData(
    sspidb.sspi_partial_api_data
)
sspi_imputed_data = mongo_wrapper.MongoWrapper(
    sspidb.sspi_imputed_data
)
sspi_analysis = mongo_wrapper.MongoWrapper(
    sspidb.sspi_analysis
)

# Production Databases -- More granular for fast queries
sspi_static_radar_data = sspi_production_data.SSPIProductionData(
    sspidb.sspi_static_radar_data
)
sspi_dynamic_line_data = sspi_production_data.SSPIProductionData(
    sspidb.sspi_dynamic_line_data
)
sspi_dynamic_matrix_data = sspi_production_data.SSPIProductionData(
    sspidb.sspi_dynamic_matrix_data
)
