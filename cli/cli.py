import click
import json
from cli.utilities import full_name
from database_connector import SSPIDatabaseConnector

@click.group()
def cli():
    pass

@cli.command()
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=False)
def query(database, indicator_code=None):
    database = full_name(database)
    session = SSPIDatabaseConnector()
    request_string = f"/api/v1/query/{database}?"
    if indicator_code:
        request_string += f"IndicatorCode={indicator_code}"
    res = session.get_data_local(request_string)
    click.echo(json.dumps(res.json()))
    return res.json()

if __name__ == "__main__":
    cli()
