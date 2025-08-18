import click
from connector import SSPIDatabaseConnector
from cli.utilities import echo_pretty
import json


@click.group(help="Get Metadata from the SSPI Database")
def metadata():
    pass


@metadata.command(help="Reload all metadata in sspi_metadata from local json")
def reload():
    """
    Get SSPI Pillar Metadata
    """
    connector = SSPIDatabaseConnector()
    url = "/api/v1/delete/clear/sspi_metadata"
    result = connector.call(url, method="DELETE")
    click.echo(result.text)
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Delete Request Failed with Status Code {
                result.status_code}"
        )
    url = "/api/v1/load/sspi_metadata"
    result = connector.call(url, method="GET")
    click.echo(result.text)
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Load Request Failed with Status Code {
                result.status_code}"
        )


@metadata.command(help="Get Pillar Metadata from the SSPI Database")
@click.argument("pillar_code", type=str, required=False)
def pillar(pillar_code):
    """Get SSPI Pillar Metadata
    """
    connector = SSPIDatabaseConnector()
    pillar_code = pillar_code.upper() if pillar_code else None
    if not pillar_code:
        url = "/api/v1/query/metadata/pillar_details"
    elif pillar_code in ["CODES", "CODE"]:
        url = "/api/v1/query/metadata/pillar_codes"
    else:
        url = f"/api/v1/query/metadata/pillar_detail/{pillar_code}"
    result = connector.call(url)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Pillar Query Failed with Status Code {
                result.status_code}"
        )


@metadata.command(help="Get Category Metadata from the SSPI Database")
@click.argument("category_code", type=str, required=False)
def category(category_code):
    """Get SSPI Category Metadata
    """
    connector = SSPIDatabaseConnector()
    category_code = category_code.upper() if category_code else None
    if not category_code:
        url = "/api/v1/query/metadata/category_details"
    elif category_code in ["CODES", "CODE"]:
        url = "/api/v1/query/metadata/category_codes"
    else:
        url = f"/api/v1/query/metadata/category_detail/{category_code}"
    result = connector.call(url)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Category Query Failed with Status Code {result.status_code}"
        )
    


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


@metadata.command(help="Get SSPI Dataset Metadata")
@click.argument("dataset_code", type=str, required=False)
def dataset(dataset_code):
    """Get SSPI Dataset Metadata
    """
    connector = SSPIDatabaseConnector()
    dataset_code = dataset_code.upper() if dataset_code else None
    if not dataset_code:
        url = "/api/v1/query/metadata/dataset_details"
    elif dataset_code in ["CODES", "CODE"]:
        url = "/api/v1/query/metadata/dataset_codes"
    else:
        url = f"/api/v1/query/metadata/dataset_detail/{dataset_code}"
    result = connector.call(url)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Dataset Query Failed with Status Code {
                result.status_code}"
        )
        echo_pretty(result.header)
        echo_pretty(result.text)


@metadata.command(help="Get SSPI Item Metadata")
@click.argument("item_code", type=str, required=False)
def item(item_code):
    """Get SSPI Item Metadata
    """
    connector = SSPIDatabaseConnector()
    item_code = item_code.upper() if item_code else None
    if not item_code:
        url = "/api/v1/query/metadata/item_details"
    elif item_code in ["CODES", "CODE"]:
        url = "/api/v1/query/metadata/item_codes"
    else:
        url = f"/api/v1/query/metadata/item_detail/{item_code}"
    result = connector.call(url)
    click.echo(json.dumps(result.json()))
    if result.status_code != 200:
        raise click.ClickException(
            f"Error! Item Query Failed with Status Code {
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
metadata.add_command(dataset)
metadata.add_command(country)
