import click
from requests.exceptions import JSONDecodeError, InvalidJSONError
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty, stream_response
import json


@click.command(help="Clean raw indicator data and compute indicator scores")
@click.argument("series_code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def compute(series_code, remote=False):
    connector = SSPIDatabaseConnector()
    series_code = series_code.upper()
    if len(series_code) != 6: 
        request_string = f"/api/v1/compute/{series_code}"
        res = connector.call(request_string, method="POST", remote=remote, stream=True)
        return stream_response(res)
    request_string = f"/api/v1/compute/{series_code}"
    res = connector.call(request_string, method="POST", remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
    try:
        click.echo(json.dumps(res.json()))
    except JSONDecodeError:
        echo_pretty("error: Invalid JSON Response")


