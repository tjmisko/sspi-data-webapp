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


@click.group()
def delete():
    pass


@delete.command()
@click.argument("database", type=str, required=True)
@click.argument("indicator_code", type=str, required=False)
def indicator(database, indicator_code=None):
    database = full_name(database)
    session = SSPIDatabaseConnector()
    res = session.delete_indicator_data_local(database, indicator_code)
    if res.status_code != 200:
        raise click.ClickException(
            f"Error! Delete Request Failed with Status Code {res.status_code}"
        )
        click.echo(res.header)
        click.echo(res.text)
    click.echo(res.text)
    return res.text


cli.add_command(delete)

if __name__ == "__main__":
    cli()
