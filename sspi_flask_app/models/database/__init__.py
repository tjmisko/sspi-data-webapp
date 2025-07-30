from flask_pymongo.wrappers import MongoClient
import logging

from sspi_flask_app.models.database.mongo_wrapper import (
    MongoWrapper
)
from sspi_flask_app.models.database.sspi_clean_api_data import (
    SSPICleanAPIData, SSPIIncompleteAPIData
)
from sspi_flask_app.models.database.sspi_main_data_v3 import (
    SSPIMainDataV3
)
from sspi_flask_app.models.database.sspi_metadata_deprecated import (
    SSPIMetadataDeprecated
)
from sspi_flask_app.models.database.sspi_metadata import (
    SSPIMetadata
)
from sspi_flask_app.models.database.sspi_item_data import (
    SSPIItemData
)
from sspi_flask_app.models.database.sspi_production_data import (
    SSPIProductionData
)
from sspi_flask_app.models.database.sspi_raw_api_data import (
    SSPIRawAPIData
)
from sspi_flask_app.models.database.sspi_indicator_data import (
    SSPIIndicatorData
)
from sspi_flask_app.models.database.sspi_indicator_data import (
    SSPIIncompleteIndicatorData
)
from sspi_flask_app.models.database.sspi_panel_data import (
    SSPIPanelData
)

logging.getLogger("pymongo").setLevel(logging.WARNING)

client = MongoClient('localhost', 27017)
sspidb = client.flask_db

sspi_metadata = SSPIMetadata(
    sspidb.sspi_metadata
)
sspi_static_metadata = SSPIMetadataDeprecated(
    sspidb.sspi_static_metadata,
    indicator_detail_file="IndicatorDetailsStatic.csv",
    intermediate_detail_file="IntermediateDetailsStatic.csv"
)
sspi_main_data_v3 = SSPIMainDataV3(
    sspidb.sspi_main_data_v3
)
sspi_raw_api_data = SSPIRawAPIData(
    sspidb.sspi_raw_api_data
)
sspi_raw_outcome_data = SSPIRawAPIData(
    sspidb.sspi_raw_outcome_data
)
sspi_score_data = SSPIItemData(
    sspidb.sspi_item_data
)
sspi_clean_api_data = SSPICleanAPIData(
    sspidb.sspi_clean_api_data
)
sspi_indicator_data = SSPIIndicatorData(
    sspidb.sspi_indicator_data
)
sspi_incomplete_indicator_data = SSPIIncompleteIndicatorData(
    sspidb.sspi_incomplete_indicator_data
)
sspi_imputed_data = MongoWrapper(
    sspidb.sspi_imputed_data
)
sspi_analysis = MongoWrapper(
    sspidb.sspi_analysis
)
sspi_panel_data = SSPIPanelData(
    sspidb.sspi_panel_data
)

# Production Data
sspi_static_rank_data = SSPIProductionData(
    sspidb.sspi_static_rank_data
)
sspi_static_corr_data = SSPIProductionData(
    sspidb.sspi_static_corr_data
)
sspi_static_radar_data = SSPIProductionData(
    sspidb.sspi_static_radar_data
)
sspi_dynamic_line_data = SSPIProductionData(
    sspidb.sspi_dynamic_line_data
)
sspi_dynamic_matrix_data = SSPIProductionData(
    sspidb.sspi_dynamic_matrix_data
)
sspi_static_stack_data = SSPIProductionData(
    sspidb.sspi_static_stack_data
)
