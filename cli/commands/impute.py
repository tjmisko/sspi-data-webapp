import click
from connector import SSPIDatabaseConnector
from cli.utilities import stream_response
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
    content_type = res.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        # Indicators without an impute route answer with a plain-text
        # event stream ("No Impute route for CODE"); echo it instead of
        # crashing on res.json().
        click.echo(res.text.strip())
        return
    click.echo(json.dumps(res.json()))
