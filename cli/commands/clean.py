import click
import json
from connector import SSPIDatabaseConnector
from cli.utilities import stream_response


@click.command(help="Clean raw data to prepare datasets")
@click.argument("series_code", type=str)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def clean(series_code, remote: bool):
    connector = SSPIDatabaseConnector()
    series_code = series_code.upper()
    request_string = f"/api/v1/clean/{series_code}"
    stream_response(connector.call(request_string, remote=remote, stream=True, timeout=300))
