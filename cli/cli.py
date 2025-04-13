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
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def query(database, indicator_code=None, remote=False):
    database = full_name(database)
    connector = SSPIDatabaseConnector()
    request_string = f"/api/v1/query/{database}?"
    if indicator_code:
        indicator_code = indicator_code.upper()
        request_string += f"IndicatorCode={indicator_code}"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Delete Query Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))


@click.group(help="Delete data from an SSPI Database")
def delete():
    pass


@delete.command()
@click.argument("database", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def duplicates(database, remote=False):
    database = full_name(database)
    connector = SSPIDatabaseConnector()
    msg = connector.delete_duplicate_data(database, remote=remote)
    echo_pretty(msg)


@delete.command()
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def indicator(database, indicator_code, remote=False):
    database = full_name(database)
    indicator_code = indicator_code.upper()
    confirm_msg_lst = [
        "Confirm ",
        click.style("DELETE", fg="red"),
        " of all observations of ",
        click.style(indicator_code, fg="red"),
        " from ",
        click.style((lambda x: "Remote" if x else "Local")(remote), fg="red"),
        " database ",
        click.style(database, fg="red")
    ]
    if click.confirm("".join(confirm_msg_lst)):
        connector = SSPIDatabaseConnector()
        msg = connector.delete_indicator_data(database, indicator_code, remote=remote)
        echo_pretty(msg)


cli.add_command(delete)


@cli.command(help="Collect raw data from source APIs")
@click.argument("indicator_code", type=str)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def collect(indicator_code, remote=False):
    connector = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    for msg in connector.collect(indicator_code, remote=remote):
        echo_pretty(msg)


@cli.command(help="Clean raw indicator data and compute indicator scores")
@click.argument("indicator_code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def compute(indicator_code, remote=False):
    connector = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    request_string = f"/api/v1/compute/{indicator_code}"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))


@cli.group(invoke_without_command=True, help="Finalize clean data for plotting")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.pass_context
def finalize(ctx, remote=False):
    if ctx.invoked_subcommand is None:
        connector = SSPIDatabaseConnector()
        for msg in connector.finalize(remote=remote):
            echo_pretty(msg)


@finalize.group(help="Finalize dynamic data")
def dynamic():
    pass


@finalize.command(help="Finalize indicator dynamic line data")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def line(remote=False):
    click.echo("Finalizing Dynamic Line Data")
    connector = SSPIDatabaseConnector()
    res = connector.call("/api/v1/production/finalize/dynamic/line", remote=remote)
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


@cli.command(help="Pull local data to remote server")
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=True)
def pull(database: str, indicator_code: str):
    database = full_name(database)
    indicator_code = indicator_code.upper()
    confirm_msg_lst = [
        "Confirm ",
        click.style("PULL", fg="yellow"),
        " of all observations of ",
        click.style(indicator_code, fg="yellow"),
        " from ",
        click.style("Remote", fg="yellow"),
        " database ",
        click.style(database, fg="yellow")
    ]
    if click.confirm("".join(confirm_msg_lst)):
        connector = SSPIDatabaseConnector()
        res = connector.call(
            f"/api/v1/pull/{database}/{indicator_code}",
            method="POST"
        )
        if res.status_code != 200:
            raise click.ClickException(
                f"Error! Finalize Request Failed with Status Code {res.status_code}"
            )
            echo_pretty(res.header)
            echo_pretty(res.text)
        echo_pretty(res.text)


@cli.command(help="Push local data to remote server")
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=True)
def push(database: str, indicator_code: str):
    database = full_name(database)
    indicator_code = indicator_code.upper()
    confirm_msg_lst = [
        "Confirm ",
        click.style("PUSH", fg="yellow"),
        " of all observations of ",
        click.style(indicator_code, fg="yellow"),
        " from ",
        click.style("Local", fg="yellow"),
        " database ",
        click.style(database, fg="yellow")
    ]
    if click.confirm("".join(confirm_msg_lst)):
        connector = SSPIDatabaseConnector()
        res = connector.call(
            f"/api/v1/push/{database}/{indicator_code}",
            method="POST"
        )
        if res.status_code != 200:
            raise click.ClickException(
                f"Error! Finalize Request Failed with Status Code {res.status_code}"
            )
            echo_pretty(res.header)
            echo_pretty(res.text)
        echo_pretty(res.text)


if __name__ == "__main__":
    cli()
