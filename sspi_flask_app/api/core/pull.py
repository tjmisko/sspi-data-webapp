from flask import Blueprint, Response
from flask_login import login_required
from sspi_flask_app.api.resources.utilities import lookup_database
from database_connector import SSPIDatabaseConnector


pull_bp = Blueprint("pull_bp", __name__,
                    template_folder="templates",
                    static_folder="static",
                    url_prefix="/pull")


@pull_bp.route("/<database_name>/<IndicatorCode>", methods=["GET"])
@login_required
def pull(database_name, IndicatorCode):
    local_database = lookup_database(database_name)
    count = local_database.delete_many({"IndicatorCode": IndicatorCode})
    message_1 = (
        f"Deleted {count} local observations of Indicator ",
        f"{IndicatorCode} from local database {database_name}\n"
    )
    print(message_1)
    connector = SSPIDatabaseConnector()
    remote_query_url = f"/api/v1/query/{
        database_name}?IndicatorCode={IndicatorCode}"
    remote_data = connector.get_data_remote(remote_query_url).json()
    local_database.insert_many(remote_data)
    message_2 = (
        f"Inserted {len(remote_data)} remote observations of Indicator ",
        f"{IndicatorCode} into local database {database_name}\n"
    )
    print(message_2)
    return Response(message_1 + message_2, mimetype="text/plain")
