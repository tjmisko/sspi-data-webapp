from sspi_flask_app.api.core.sspi import collect_bp
from flask_login import login_required, current_user
from flask import Blueprint, Response
from flask_login import current_user, login_required
import requests
import time
from sspi_flask_app.models.database import sspi_raw_outcome_data


@collect_bp.route("/outcome/GDPMER", methods=['GET'])
@login_required
def gdpmek():
    """Collect GDP per Capita at Market Exchange Rate from World Bank API"""
    def collectWorldBankOutcomeData(WorldBankIndicatorCode, IndicatorCode, **kwargs):
        yield "Collecting data for World Bank Indicator" + \
            "{WorldBankIndicatorCode}\n"
        url_source = (
            "https://api.worldbank.org/v2/country/all/"
            f"indicator/{WorldBankIndicatorCode}?format=json"
        )
        response = requests.get(url_source).json()
        total_pages = response[0]['pages']
        for p in range(1, total_pages + 1):
            new_url = f"{url_source}&page={p}"
            yield f"Sending Request for page {p} of {total_pages}\n"
            response = requests.get(new_url).json()
            document_list = response[1]
            count = sspi_raw_outcome_data.raw_insert_many(
                document_list, IndicatorCode, **kwargs)
            yield f"Inserted {count} new observations into sspi_outcome_data\n"
            time.sleep(0.5)
        yield f"Collection complete for World Bank Indicator {WorldBankIndicatorCode}"

    def collect_iterator(**kwargs):
        # insert UN population data into sspi_country_characteristics database
        yield from collectWorldBankOutcomeData("NY.GDP.PCAP.CD", "GDPMER", **kwargs)

    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')
