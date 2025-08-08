import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name
import json


@click.command(help="Query an SSPI Database")
@click.argument("database", type=str, required=True)
@click.argument("series_codes", type=str, required=False, nargs=-1)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def query(database, series_codes: list[str]=[], remote=False):
    database = full_name(database)
    connector = SSPIDatabaseConnector()
    request_string = f"/api/v1/query/{database}?"
    if series_codes:
        for sc in series_codes:
            new_series = f"&SeriesCode={sc.upper()}"
            if request_string.endswith("?"):
                request_string += new_series[1:]
            else:
                request_string += new_series
    # Use longer timeout for raw data queries which contain large documents
    timeout = 300 if database == "sspi_raw_api_data" else 120
    res = connector.call(request_string, remote=remote, timeout=timeout)
    click.echo(json.dumps(res.json()))
