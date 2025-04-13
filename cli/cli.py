import click
import json
from cli.utilities import (
    full_name,
    echo_pretty
)
from connector import SSPIDatabaseConnector


@click.group()
def cli():
    pass


@cli.command(help="Query an SSPI Database")
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=False)
def query(database, indicator_code=None):
    database = full_name(database)
    session = SSPIDatabaseConnector()
    request_string = f"/api/v1/query/{database}?"
    if indicator_code:
        indicator_code = indicator_code.upper()
        request_string += f"IndicatorCode={indicator_code}"
    res = session.get_data_local(request_string)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Delete Query Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))
    return res.json()


@click.group(help="Delete data from an SSPI Database")
def delete():
    pass


@delete.command()
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=True)
def indicator(database, indicator_code):
    database = full_name(database)
    indicator_code = indicator_code.upper()
    session = SSPIDatabaseConnector()
    res = session.delete_indicator_data_local(database, indicator_code)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Delete Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    echo_pretty(res.text)


cli.add_command(delete)


@cli.command(help="Collect raw data from source APIs")
@click.argument("indicator_code", type=str)
def collect(indicator_code):
    session = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    for msg in session.collect_data_local(indicator_code):
        echo_pretty(msg)


@cli.command(help="Clean raw indicator data and compute indicator scores")
@click.argument("indicator_code", type=str, required=True)
def compute(indicator_code):
    session = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    request_string = f"/api/v1/compute/{indicator_code}"
    res = session.get_data_local(request_string)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))
    return res.json()


@cli.group(invoke_without_command=True, help="Finalize clean data for plotting")
@click.pass_context
def finalize(ctx):
    if ctx.invoked_subcommand is None:
        session = SSPIDatabaseConnector()
        for msg in session.finalize_data_local():
            echo_pretty(msg)


@finalize.group(help="Finalize dynamic data")
def dynamic():
    pass


@finalize.command(help="Finalize indicator dynamic line data")
def line():
    click.echo("Finalizing Dynamic Line Data")
    session = SSPIDatabaseConnector()
    res = session.call_local("/api/v1/production/finalize/dynamic/line")
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Finalize Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.secho("Finalization Complete", fg="green")


dynamic.add_command(line)
finalize.add_command(dynamic)
cli.add_command(finalize)


if __name__ == "__main__":
    cli()
