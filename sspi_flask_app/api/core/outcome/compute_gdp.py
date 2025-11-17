from flask_login import login_required
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_outcome_data)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
)


# @compute_bp.route("/outcome/GDPMER", methods=['POST'])
# @admin_required
# def compute_gdpmer():
#     app.logger.info("Running /api/v1/compute/outcome/GDPMER")
#     sspi_clean_outcome_data.delete_many({"IndicatorCode": "GDPMER"})
#     gdpmer_raw = sspi_raw_outcome_data.fetch_raw_data("GDPMER")
#     extracted_data = []
#     for obs in gdpmer_raw:
#         value = obs["Raw"]["value"]
#         if not value or value == "None" or value == "null":
#             continue
#         if not len(obs["Raw"]["countryiso3code"]) == 3:
#             continue
#         extracted_data.append({
#             "CountryCode": obs["Raw"]["countryiso3code"],
#             "IndicatorCode": "GDPMER",
#             "Year": int(obs["Raw"]["date"]),
#             "Value": float(obs["Raw"]["value"]),
#             "Unit": obs["Raw"]["indicator"]["value"],
#             "Score": float(obs["Raw"]["value"])
#         })
#     sspi_clean_outcome_data.insert_many(extracted_data)
#     return parse_json(extracted_data)


# @compute_bp.route("/outcome/GDPPPP", methods=['POST'])
# @admin_required
# def compute_gdpppp():
#     app.logger.info("Running /api/v1/compute/INTRNT")
#     sspi_clean_api_data.delete_many({"IndicatorCode": "INTRNT"})
#     gdpppp_raw = sspi_raw_outcome_data.fetch_raw_data("GDPPPP")
#     extracted_data = []
#     for obs in gdpppp_raw:
#         value = obs["Raw"]["value"]
#         if not value or value == "None" or value == "null":
#             continue
#         if not len(obs["Raw"]["countryiso3code"]) == 3:
#             continue
#         extracted_data.append({
#             "CountryCode": obs["Raw"]["countryiso3code"],
#             "IndicatorCode": "GDPPPP",
#             "Year": int(obs["Raw"]["date"]),
#             "Value": float(obs["Raw"]["value"]),
#             "Unit": obs["Raw"]["indicator"]["value"],
#             "Score": float(obs["Raw"]["value"])
#         })
#     sspi_clean_outcome_data.insert_many(extracted_data)
#     return parse_json(extracted_data)
