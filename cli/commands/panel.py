import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty, stdin_is_empty, stream_response
import json


@click.group()
def panel():
    """Group of commands for plotting data"""
    pass


@panel.command(help="Return the levels of the data from stdin")
@click.option('--exclude', "-e", multiple=True, required=False, help="List of strings to exclude")
def levels(exclude: list[str]):
    """Read data from standard input generate """
    if stdin_is_empty():
        raise click.ClickException("No input provided")
    data = click.get_text_stream("stdin").read()
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON input")
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/panel/levels"
    if exclude:
        request_string += "?"
        for e in exclude:
            request_string += f"exclude={e}&"
        request_string = request_string[:-1]
    res = connector.call(request_string, method="POST", data=data)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Panel Plot Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))


@panel.command(help="Plot country-year panel data given in stdin")
@click.option('--exclude', "-e", multiple=True, required=False, help="List of strings to exclude")
def plot(exclude: list[str]):
    """Read data from standard input generate """
    if stdin_is_empty():
        raise click.ClickException("No input provided")
    data = click.get_text_stream("stdin").read()
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON input")
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/panel/plot"
    if exclude:
        request_string += "?"
        for e in exclude:
            request_string += f"exclude={e}&"
        request_string = request_string[:-1]
    res = connector.call(request_string, method="POST", data=data, stream=True)
    stream_response(res)
