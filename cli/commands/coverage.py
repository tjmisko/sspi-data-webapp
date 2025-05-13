import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty
import json


@click.command(help="Compute data coverage")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def coverage(remote=False):
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/coverage"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))
