import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name, echo_pretty


@click.command(help="Push local data to remote server")
@click.argument("database", type=str, required=True)
@click.argument("series_code", type=str, required=True)
@click.option("--yes-to-all", "-y", is_flag=True, help="Skip confirmation prompt")
def push(database: str, series_code: str, yes_to_all: bool):
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
    if yes_to_all or click.confirm("".join(confirm_msg_lst)):
        connector = SSPIDatabaseConnector()
        query_url = f"/api/v1/query/{database}?SeriesCode={series_code}"
        query_res = connector.call(query_url)
        local_data = query_res.json()
        echo_pretty((
            f"Sourced {len(local_data)} local observations of Indicator "
            f"{series_code} from local database {database}\n"
        ))
        if not local_data:
            echo_pretty((
                f"error: No local observations of Indicator {series_code} "
                f"found in local database {database}\n"
            ))
            return
        url = f"/api/v1/delete/series/{database}/{series_code}"
        res_1 = connector.call(url, remote=True, method="DELETE")
        click.secho(str(res_1.text) + "\n")
        res_2 = connector.load(
            local_data, database, remote=True
        )
        echo_pretty(str(res_2.text) + "\n")
