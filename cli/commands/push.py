import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name, echo_pretty


def count_remote_observations(connector, query_url):
    """Return the number of remote observations matching query_url, or None
    when the remote query fails or does not return a list."""
    try:
        remote_res = connector.call(query_url, remote=True)
        remote_data = remote_res.json()
    except Exception:
        return None
    if not isinstance(remote_data, list):
        return None
    return len(remote_data)


def delete_remote_series(connector, database, series_code):
    url = f"/api/v1/delete/series/{database}/{series_code}"
    res = connector.call(url, remote=True, method="DELETE")
    click.secho(str(res.text) + "\n")


def handle_empty_local_series(connector, database, series_code, query_url, delete_remote_if_empty):
    """An empty local set means the series was cleared locally (for example,
    re-imputation that now needs no imputed rows). Pushing nothing must not
    silently leave the old remote rows in place."""
    remote_count = count_remote_observations(connector, query_url)
    if remote_count == 0:
        echo_pretty((
            f"No local or remote observations of Indicator {series_code} "
            f"in database {database}; nothing to push\n"
        ))
        return
    remote_count_text = "an unknown number of" if remote_count is None else str(remote_count)
    click.secho((
        f"WARNING: No local observations of {series_code} in {database}, "
        f"but Remote {database} holds {remote_count_text} observations of "
        f"{series_code}. Those remote rows are stale."
    ), fg="red", bold=True)
    delete_confirmed = delete_remote_if_empty or click.confirm(
        f"Delete all Remote observations of {series_code} from {database} "
        "so Remote matches the empty local set?",
        default=False,
    )
    if delete_confirmed:
        delete_remote_series(connector, database, series_code)
        return
    click.secho((
        f"Remote observations of {series_code} were LEFT IN PLACE in {database}. "
        f"Remove them with: sspi delete series {database} {series_code} -r"
    ), fg="red", bold=True)


@click.command(help="Push local data to remote server")
@click.argument("database", type=str, required=True)
@click.argument("series_code", type=str, required=True)
@click.option("--yes-to-all", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--delete-remote-if-empty",
    is_flag=True,
    help="When no local observations exist, delete the remote series without asking",
)
def push(database: str, series_code: str, yes_to_all: bool, delete_remote_if_empty: bool):
    database = full_name(database)
    series_code = series_code.upper()
    confirm_msg_lst = [
        "Confirm ",
        click.style("PUSH", fg="yellow"),
        " of all observations of ",
        click.style(series_code, fg="yellow"),
        " from ",
        click.style("Local", fg="yellow"),
        " database ",
        click.style(database, fg="yellow")
    ]
    if not (yes_to_all or click.confirm("".join(confirm_msg_lst))):
        return
    connector = SSPIDatabaseConnector()
    query_url = f"/api/v1/query/{database}?SeriesCode={series_code}"
    query_res = connector.call(query_url)
    local_data = query_res.json()
    if not isinstance(local_data, list):
        echo_pretty((
            f"error: Local query for {series_code} in {database} failed: "
            f"{local_data}\n"
        ))
        return
    echo_pretty((
        f"Sourced {len(local_data)} local observations of Indicator "
        f"{series_code} from local database {database}\n"
    ))
    if not local_data:
        handle_empty_local_series(
            connector, database, series_code, query_url, delete_remote_if_empty
        )
        return
    delete_remote_series(connector, database, series_code)
    res_2 = connector.load(
        local_data, database, remote=True
    )
    echo_pretty(str(res_2.text) + "\n")
