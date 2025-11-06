from flask import Blueprint, Response, current_app as app
from flask_login import login_required
from sspi_flask_app.api.resources.utilities import lookup_database
from connector import SSPIDatabaseConnector


sync_bp = Blueprint(
    "sync_bp", __name__,
    template_folder="templates",
    static_folder="static"
)


@sync_bp.route("/pull/<database_name>/<series_code>", methods=["POST"])
@login_required
def pull(database_name, series_code):
    connector = SSPIDatabaseConnector()
    local_database = lookup_database(database_name)
    delete_url = f"/api/v1/delete/series/{local_database.name}/{series_code}"
    res = connector.call(delete_url)
    message_1 = res.text
    app.logger.info(message_1)
    remote_query_url = (
        f"/api/v1/query/{database_name}?"
        f"series_code={series_code}"
    )
    remote_data = connector.call(remote_query_url, remote=True).json()
    local_database.insert_many(remote_data)
    message_2 = (
        f"Inserted {len(remote_data)} remote observations of Indicator "
        f"{series_code} into local database {database_name}\n"
    )
    app.logger.info(message_2)
    return Response(message_1 + message_2, mimetype="text/plain")


@sync_bp.route("/push/<database_name>/<series_code>", methods=["POST"])
@login_required
def push(database_name, series_code):
    def push_iterator():
        local_database = lookup_database(database_name)
        connector = SSPIDatabaseConnector()
        query_url = f"/api/v1/query/{local_database.name}?SeriesCode={series_code}"
        query_res = connector.call(query_url)
        local_data = query_res.json()
        yield (
            f"Sourced {len(local_data)} local observations of Indicator "
            f"{series_code} from local database {database_name}\n"
        )
        if not local_data:
            yield (
                f"error: No local observations of Indicator {series_code} "
                f"found in local database {database_name}\n"
            )
            return
        url = f"/api/v1/delete/series/{local_database.name}/{series_code}"
        res_1 = connector.call(url, remote=True, method="DELETE")
        yield str(res_1.text) + "\n"
        res_2 = connector.load(
            local_data, database_name, remote=True
        )
        yield str(res_2.text) + "\n"
    return Response(
        push_iterator(),
        mimetype="text/event-stream"
    )
