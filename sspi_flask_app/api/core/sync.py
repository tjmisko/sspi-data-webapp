from flask import Blueprint, Response, current_app as app
from flask_login import login_required
from sspi_flask_app.api.resources.utilities import lookup_database
from connector import SSPIDatabaseConnector


sync_bp = Blueprint(
    "sync_bp", __name__,
    template_folder="templates",
    static_folder="static"
)


@sync_bp.route("/pull/<database_name>/<IndicatorCode>", methods=["POST"])
@login_required
def pull(database_name, IndicatorCode):
    local_database = lookup_database(database_name)
    count = local_database.delete_many({"IndicatorCode": IndicatorCode})
    message_1 = (
        f"Deleted {count} local observations of Indicator "
        f"{IndicatorCode} from local database {database_name}\n"
    )
    app.logger.info(message_1)
    connector = SSPIDatabaseConnector()
    remote_query_url = (
        f"/api/v1/query/{database_name}?"
        f"IndicatorCode={IndicatorCode}"
    )
    remote_data = connector.call(remote_query_url, remote=True).json()
    local_database.insert_many(remote_data)
    message_2 = (
        f"Inserted {len(remote_data)} remote observations of Indicator "
        f"{IndicatorCode} into local database {database_name}\n"
    )
    app.logger.info(message_2)
    return Response(message_1 + message_2, mimetype="text/plain")


@sync_bp.route("/push/<database_name>/<IndicatorCode>", methods=["POST"])
@login_required
def push(database_name, IndicatorCode):
    local_database = lookup_database(database_name)
    local_data = local_database.find(
        {"IndicatorCode": IndicatorCode}, {"_id": 0}
    )
    message_1 = (
        f"Sourced {len(local_data)} local observations of Indicator "
        f"{IndicatorCode} from local database {database_name}\n"
    )
    app.logger.info(message_1)
    connector = SSPIDatabaseConnector()
    remote_delete_msg = connector.delete_indicator_data(
        database_name, IndicatorCode, remote=True
    )
    app.logger.info(remote_delete_msg)
    remote_delete_msg = connector.load(
        local_data, database_name, IndicatorCode, remote=True
    )
    app.logger.info(remote_delete_msg)
    return Response(
        "Completed Database Push\n",
        mimetype="text/plain"
    )
