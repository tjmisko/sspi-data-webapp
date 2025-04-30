import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name
import json


@click.command(help="Query an SSPI Database")
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
