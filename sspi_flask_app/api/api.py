from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required
from .. import sspi_raw_api_data, sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_dynamic_data, sspi_imputed_data, sspi_bulk_data
from bson import json_util
import json
import math
from datetime import datetime

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)

# some common utility functions used across the api core functionality
