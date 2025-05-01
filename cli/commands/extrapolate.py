import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty, stdin_is_empty
import json


@click.group(help="Extrapolate missing data for a given indicator")
def extrapolate():
    pass


@extrapolate.command(help="Extrapolate backward from first observation for a given indicator")
@click.argument("year", type=int)
def backward(year):
    """Read data from standard input and extrapolate backward missing data for a given indicator"""
    if stdin_is_empty():
        raise click.ClickException("No input provided")
    data = click.get_text_stream("stdin").read()
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON input")
    connector = SSPIDatabaseConnector()
    request_string = f"/api/v1/utilities/extrapolate/backward/{year}"
    res = connector.call(request_string, method="POST", data=data)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Backward Extrapolation Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))


@extrapolate.command(help="Extrapolate forward from last observation for a given indicator")
@click.argument("year", type=int)
def forward(year):
    """Read data from standard input and extrapolate backward missing data for a given indicator"""
    if stdin_is_empty():
        raise click.ClickException("No input provided")
    data = click.get_text_stream("stdin").read()
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON input")
    connector = SSPIDatabaseConnector()
    request_string = f"/api/v1/utilities/extrapolate/forward/{year}"
    res = connector.call(request_string, method="POST", data=data)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Forward Extrapolation Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))
