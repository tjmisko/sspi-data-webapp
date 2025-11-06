import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name, echo_pretty


@click.command(help="Pull local data to remote server")
@click.argument("database", type=str, required=True)
@click.argument("series_code", type=str, required=True)
def pull(database: str, series_code: str):
    database = full_name(database)
    series_code = series_code.upper()
    confirm_msg_lst = [
        "Confirm ",
        click.style("PULL", fg="yellow"),
        " of all observations of ",
        click.style(series_code, fg="yellow"),
        " from ",
        click.style("Remote", fg="yellow"),
        " database ",
        click.style(database, fg="yellow")
    ]
    if click.confirm("".join(confirm_msg_lst)):
        connector = SSPIDatabaseConnector()
        delete_url = f"/api/v1/delete/series/{database}/{series_code}"
        res = connector.call(delete_url)
        message_1 = res.text
        remote_query_url = f"/api/v1/query/{database}?SeriesCode={series_code}"
        remote_data = connector.call(remote_query_url, remote=True).json()
        connector.load(remote_data, database)
        message_2 = (
            f"Inserted {len(remote_data)} remote observations of Indicator "
            f"{series_code} into local database {database}\n"
        )
        if res.status_code != 200:
            raise click.ClickException(
                f"Error! Finalize Request Failed with Status Code { res.status_code}")
        echo_pretty(res.text)
