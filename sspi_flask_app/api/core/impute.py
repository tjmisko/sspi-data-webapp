from flask import Blueprint, request
from ... import sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_raw_api_data, sspi_imputed_data
from ..resources.utilities import parse_json


impute_bp = Blueprint("impute_bp", __name__,
                      template_folder="templates",
                      static_folder="static",
                      url_prefix="/impute")

###################################
# IMPLEMENT IMPUTE FUNCITONS HERE #
###################################

# Impute should take csv data and process it into the proper form
# It should also accept JSON data, properly formatted
# We should be able to overwrite data from here 
#   - How to handle overwriting existing data?