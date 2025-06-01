import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty
import json


@click.group(invoke_without_command=True, help="Get data coverage information")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--group", "-g", type=str, help="CountryGroup (default: SSPI67)")
@click.pass_context
def coverage(ctx, remote=False, group="SSPI67"):
    if ctx.invoked_subcommand is None:
        connector = SSPIDatabaseConnector()
        url = "/api/v1/utilities/coverage"
        if group:
            url += f"?CountryGroup={group}"
        res = connector.call(url, remote=remote)
        if res.status_code != 200:
            raise click.ClickException(
                f"Error! Compute Request Failed with Status Code {res.status_code}"
            )
        click.echo(json.dumps(res.json()))


@coverage.command(help="Retrieve the list of indicators for which data coverage is complete")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--group", "-g", type=str, help="CountryGroup (default: SSPI67)")
def complete(remote=False, group="SSPI67"):
    """
    Retrieve the list of indicators for which data coverage is complete.
    :param remote: If True, send the request to the remote server.
    :param group: The country group to check coverage for (default: SSPI67).
    """
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/coverage/complete"
    if group:
        request_string += f"?CountryGroup={group}"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
    click.echo(json.dumps(res.json()))


@coverage.command(help="Retrieve the list of indicators for which data coverage is incomplete")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--group", "-g", type=str, help="CountryGroup (default: SSPI67)")
def incomplete(remote=False, group="SSPI67"):
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/coverage/incomplete"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
    click.echo(json.dumps(res.json()))


@coverage.command(help="Retrieve the list of indicators for which no data is available")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--group", "-g", type=str, help="CountryGroup (default: SSPI67)")
def unimplemented(remote=False, group="SSPI67"):
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/coverage/unimplemented"
    if group:
        request_string += f"?CountryGroup={group}"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
        echo_pretty(res.header)
        echo_pretty(res.text)
    click.echo(json.dumps(res.json()))


@coverage.command(help="Generate a coverage report for a specific indicator")
@click.argument("code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--group", "-g", type=str, help="CountryGroup (default: SSPI67)")
def report(code, remote=False, group="SSPI67"):
    """
    Generate a coverage report for a specific indicator.
    :param code: The code of the indicator or country to generate the report for.
    """
    connector = SSPIDatabaseConnector()
    code = code.upper()
    if len(code) == 3:
        request_string = f"/api/v1/utilities/coverage/report/country/{code}"
    elif len(code) == 6:
        request_string = f"/api/v1/utilities/coverage/report/indicator/{code}"
    else:
        raise click.ClickException((
            "Invalid Code Error! The code must be either 3 characters (for a "
            "country) or 6 characters (for an indicator)."
        ))
    if group:
        request_string += f"?CountryGroup={group}"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
    msg = res.text
    lines = msg.splitlines()
    for line in lines:
        if "has complete coverage" in line:
            click.secho(line, fg="green")
        else:
            echo_pretty(line)


@coverage.command(help="Retrieve the list of indicators for which data coverage is complete")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--group", "-g", type=str, help="CountryGroup (default: SSPI67)")
def schema(remote=False, group="SSPI67"):
    """
    Retrieve the list of indicators for which data coverage is complete.
    :param remote: If True, send the request to the remote server.
    :param group: The country group to check coverage for (default: SSPI67).
    """
    connector = SSPIDatabaseConnector()
    request_string = "/api/v1/utilities/coverage/schema"
    if group:
        request_string += f"?CountryGroup={group}"
    res = connector.call(request_string, remote=remote)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Compute Request Failed with Status Code {res.status_code}"
        )
    click.echo(json.dumps(res.json()))


