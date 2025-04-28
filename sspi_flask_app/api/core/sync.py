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
    def push_iterator():
        local_database = lookup_database(database_name)
        local_data = local_database.find(
            {"IndicatorCode": IndicatorCode}, {"_id": 0}
        )
        yield (
            f"Sourced {len(local_data)} local observations of Indicator "
            f"{IndicatorCode} from local database {database_name}\n"
        )
        if not local_data:
            yield (
                f"error: No local observations of Indicator {IndicatorCode} "
                f"found in local database {database_name}\n"
            )
            return
        connector = SSPIDatabaseConnector()
        url = f"/api/v1/delete/indicator/{local_database.name}/{IndicatorCode}"
        res_1 = connector.call(url, remote=True, method="DELETE")
        yield str(res_1.text) + "\n"
        res_2 = connector.load(
            local_data, database_name, IndicatorCode, remote=True
        )
        yield str(res_2.text) + "\n"
    return Response(
        push_iterator(),
        mimetype="event-stream"
    )
