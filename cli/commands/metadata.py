import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty
import json


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


@metadata.command(help="Get SSPI Item Metadata")
@click.argument("item_code", type=str, required=False)
def item(item_code):
    """Get SSPI Intermediate Metadata
    """
    connector = SSPIDatabaseConnector()
    item_code = item_code.upper() if item_code else None
    url = f"/api/v1/query/metadata/item_detail/{item_code}"
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
