import click
import json
from cli.utilities import echo_pretty
from connector import SSPIDatabaseConnector


@click.command(help="Query Country Attributes and Data")
@click.argument("country_code", type=str, required=True)
@click.argument("remote", type=str, required=False)
def country(country_code, remote = True):
    connector = SSPIDatabaseConnector()
    country_code = country_code.upper()
    request_string = f"/api/v1/query/metadata/country_detail/{country_code}"
    res = connector.call(request_string, remote=remote, stream=True)
    if res.status_code != 200:
        echo_pretty(f"error: {res.text}")
    click.echo(json.dumps(res.json()))
    
