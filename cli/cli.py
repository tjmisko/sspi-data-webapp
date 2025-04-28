import click
import json
from cli.utilities import (
    full_name,
    echo_pretty,
    stream_response,
    require_confirmation,
    open_browser_subprocess
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
    click.echo(json.dumps(res.json()))


@click.group(help="Get Metadata from the SSPI Database")
def metadata():
    pass


@metadata.group(help="Get Pillar Metadata from the SSPI Database")
def pillar():
    pass


@metadata.group(help="Get Category Metadata from the SSPI Database")
def category():
    pass


@metadata.command(help="Get SSPI Indicator Metadata")
@click.argument("indicator_code", type=str, required=False)
def indicator(indicator_code):
    """Get SSPI Indicator Metadata
    """
    connector = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper() if indicator_code else None
    if not indicator_code:
        url = "/api/v1/query/metadata/indicator_details"
    elif indicator_code in ["CODES", "CODE"]:
        url = "/api/v1/query/metadata/indicator_codes"
    else:
        url = f"/api/v1/query/metadata/indicator_detail/{indicator_code}"
    result = connector.call(url)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Indicator Query Failed with Status Code {result.status_code}"
        )
        echo_pretty(result.header)
        echo_pretty(result.text)


@metadata.command(help="Get SSPI Intermediate Metadata")
@click.argument("intermediate_code", type=str, required=False)
def intermediate(intermediate_code):
    """Get SSPI Intermediate Metadata
    """
    connector = SSPIDatabaseConnector()
    intermediate_code = intermediate_code.upper() if intermediate_code else None
    if not intermediate_code:
        url = "/api/v1/query/metadata/intermediate_details"
    elif intermediate_code in ["CODES", "CODE"]:
        url = "/api/v1/query/metadata/intermediate_codes"
    else:
        url = f"/api/v1/query/metadata/intermediate_detail/{intermediate_code}"
    result = connector.call(url)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Intermediate Query Failed with Status Code {
                result.status_code}"
        )
        echo_pretty(result.header)
        echo_pretty(result.text)


@metadata.group(help="Get Country Metadata from the SSPI Database")
def country():
    pass


@country.command(help="Get SSPI Country Group Names and Members")
@click.argument("group_code", type=str, required=False)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def group(group_code=None, remote=False):
    connector = SSPIDatabaseConnector()
    group_code = group_code.upper() if group_code else None
    if not group_code:
        url = "/api/v1/query/metadata/country_groups"
    elif group_code in ["ALL", "DUMP", "TREE"]:
        url = "/api/v1/query/metadata/country_groups?tree=true"
    else:
        url = f"/api/v1/query/metadata/country_group/{group_code}"
    result = connector.call(url, remote=remote)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Country Group Query Failed with Status Code {
                result.status_code}"
        )
        echo_pretty(result.header)
        echo_pretty(result.text)


metadata.add_command(pillar)
metadata.add_command(category)
metadata.add_command(indicator)
metadata.add_command(intermediate)
metadata.add_command(country)
cli.add_command(metadata)


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
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def clear(database, remote=False):
    """Clear contents of database
    """
    connector = SSPIDatabaseConnector()
    prompt_lst = [
        "Confirm ",
        click.style("CLEAR", fg="red"),
        " of all observations from ",
        click.style("Local", fg="red"),
        " database ",
        click.style(database, fg="red"),
        ".\n\nType {0} to confirm deletion"
    ]
    if require_confirmation(phrase=database, prompt="".join(prompt_lst)):
        msg = connector.clear_database(database, database, remote=remote)
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
        endpoint = f"/api/v1/delete/indicator/{database}/{indicator_code}"
        res = connector.call(endpoint, remote=remote, method="DELETE")
        echo_pretty(res.text)


cli.add_command(delete)


@cli.command(help="Collect raw data from source APIs")
@click.argument("indicator_code", type=str)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def collect(indicator_code, remote=False):
    connector = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    request_string = f"/api/v1/collect/{indicator_code}"
    stream_response(connector.call(request_string, remote=remote, stream=True))


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
        url = "/api/v1/production/finalize"
        stream_response(connector.call(url, remote=remote, stream=True))


@finalize.group(help="Finalize dynamic data")
def dynamic():
    pass


@finalize.command(help="Finalize indicator dynamic line data")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def line(remote=False):
    click.echo("Finalizing Dynamic Line Data")
    connector = SSPIDatabaseConnector()
    url = "/api/v1/production/finalize/dynamic/line"
    stream_response(connector.call(url, remote=remote, stream=True))
    click.secho("\nFinalization Complete", fg="green")


@finalize.command(help="Finalize indicator dynamic matrix data")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def overview(remote=False):
    click.echo("Finalizing Dynamic Line Data")
    connector = SSPIDatabaseConnector()
    url = "/api/v1/production/finalize/dynamic/matrix"
    stream_response(connector.call(url, remote=remote, stream=True))
    click.secho("\nFinalization Complete", fg="green")


dynamic.add_command(overview)
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
                f"Error! Finalize Request Failed with Status Code {
                    res.status_code}"
            )
            echo_pretty(res.header)
            echo_pretty(res.text)
        echo_pretty(res.text)


@cli.command(help="Push local data to remote server")
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=True)
@click.option("--yes-to-all", "-y", is_flag=True, help="Skip confirmation prompt")
def push(database: str, indicator_code: str, yes_to_all: bool):
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
    if yes_to_all or click.confirm("".join(confirm_msg_lst)):
        connector = SSPIDatabaseConnector()
        exit_code = stream_response(connector.call(
            f"/api/v1/push/{database}/{indicator_code}",
            method="POST",
            stream=True
        ))
        if exit_code == 0:
            click.secho("\nPush Complete", fg="green")
        else:
            click.secho("\nPush Failed", fg="red")


class DefaultGroup(click.Group):
    def resolve_command(self, ctx, args):
        try:
            # normal dispatch — works for “repo”, “project”, etc.
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # unknown token → treat it as an IDCODE and fall back
            idcode = args[0]
            if len(args) == 1 and len(idcode) == 6:
                return (
                    'line',
                    self.get_command(ctx, 'line'),
                    args
                )
            # anything else really is an error
            raise click.UsageError("Invalid command or IDCODE")


@cli.group(cls=DefaultGroup, invoke_without_command=True, help="View data visualizations")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.pass_context
def view(ctx, remote=False):
    if ctx.invoked_subcommand is None:
        connector = SSPIDatabaseConnector()
        url = connector.remote_base if remote else connector.local_base
        open_browser_subprocess(url)


@view.command(help="View line chart")
@click.argument("idcode", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def line(idcode, remote=False):
    """
    Open a LINE chart plotting IDCODE by Year

    IDCODE is the IndicatorCode, IntermediateCode, PillarCode, CategoryCode,
    PillarCode, or CountryCode for the chart
    """
    connector = SSPIDatabaseConnector()
    base_url = connector.remote_base if remote else connector.local_base
    url = base_url + "/api/v1/view/line/" + idcode
    open_browser_subprocess(url)


@view.command(help="View line chart")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def overview(remote=False):
    """Open DATA OVERVIEW chart
    """
    connector = SSPIDatabaseConnector()
    base_url = connector.remote_base if remote else connector.local_base
    url = base_url + "/api/v1/view/overview"
    open_browser_subprocess(url)


@view.command(help="View GitHub Project")
def project():
    """Open GitHub Project in browser
    """
    url = "https://github.com/users/tjmisko/projects/4/views/1"
    open_browser_subprocess(url)


@view.command(help="View 2018 Paper")
def paper():
    """Open working paper page in browser
    """
    url = "https://irle.berkeley.edu/publications/working-papers/national-policies-to-support-sustainable-equitable-economies/"
    open_browser_subprocess(url)


@view.command(help="View Indicator Details")
def details():
    """Open GitHub Project in browser
    """
    url = "https://docs.google.com/spreadsheets/d/1nL0BwtKFvb7SXjPyMlbYCWyGtzQrRXRl_gM05-9ghGI/edit?gid=0#gid=0"
    open_browser_subprocess(url)


@view.command(help="View GitHub Repo")
def repo():
    """Open GitHub Project in browser
    """
    url = "https://github.com/tjmisko/sspi-data-webapp"
    open_browser_subprocess(url)


view.add_command(line)
cli.add_command(view)
