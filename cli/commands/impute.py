import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty, stream_response
import json


@click.command(help="Impute missing values in indicator data")
@click.argument("series_code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def impute(series_code, remote=False):
    connector = SSPIDatabaseConnector()
    series_code = series_code.upper()
    if len(series_code) != 6:
        request_string = f"/api/v1/impute/{series_code}"
        res = connector.call(request_string, method="POST", remote=remote, stream=True)
        return stream_response(res)
    request_string = f"/api/v1/impute/{series_code}"
    res = connector.call(request_string, method="POST", remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Impute Request Failed with Status Code {res.status_code}"
        )
    click.echo(json.dumps(res.json()))
