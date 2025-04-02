from flask import Blueprint, Response, current_app as app
from flask_login import login_required
from sspi_flask_app.api.resources.utilities import lookup_database
from database_connector import SSPIDatabaseConnector


sync_bp = Blueprint(
    "sync_bp", __name__,
    template_folder="templates",
    static_folder="static"
)


@sync_bp.route("/pull/<database_name>/<IndicatorCode>", methods=["GET"])
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
    remote_query_url = f"/api/v1/query/{
        database_name}?IndicatorCode={IndicatorCode}"
    remote_data = connector.get_data_remote(remote_query_url).json()
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
    local_data = local_database.find({"IndicatorCode": IndicatorCode})
    message_1 = (
        f"Sourced {len(local_data)} local observations of Indicator "
        f"{IndicatorCode} from local database {database_name}\n"
    )
    app.logger.info(message_1)
    connector = SSPIDatabaseConnector()
    remote_delete = connector.delete_indicator_data_remote(
        database_name, IndicatorCode
    )
    if remote_delete.status_code != 200:
        app.logger.error(f"Failed to delete remote data\n{remote_delete.text}")
        return Response(
            remote_delete.text,
            status=remote_delete.status_code, mimetype="text/plain"
        )
    remote_data = connector.load_json_remote(
        local_data, database_name, IndicatorCode
    )
    if remote_data.status_code != 200:
        app.logger.error(f"Failed to upload new remote data\n{remote_delete.text}")
        return Response(
            remote_delete.text,
            status=remote_delete.status_code, mimetype="text/plain"
        )
    message_2 = (
        f"Inserted {len(remote_data)} local observations of Indicator ",
        f"{IndicatorCode} into remote database {database_name}\n"
    )
    app.logger.info(message_1 + message_2)
    return Response(message_1 + message_2, mimetype="text/plain")
