import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty
import json


@click.command(help="Clean raw indicator data and compute indicator scores")
@click.argument("indicator_code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def compute(indicator_code, remote=False):
    connector = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    request_string = f"/api/v1/compute/{indicator_code}"
    res = connector.call(request_string, method="POST", remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))
