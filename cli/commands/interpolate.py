import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty, stdin_is_empty
import json


@click.group(help="Interpolate missing data for a given indicator")
def interpolate():
    pass


@interpolate.command(help="Extrapolate backward from first observation for a given indicator")
def linear():
    """Read data from standard input and linearly interpolate missing data for a given indicator"""
    if stdin_is_empty():
        raise click.ClickException("No input provided")
    data = click.get_text_stream("stdin").read()
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON input")
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/interpolate/linear"
    res = connector.call(request_string, method="POST", data=data)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Backward Extrapolation Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))
