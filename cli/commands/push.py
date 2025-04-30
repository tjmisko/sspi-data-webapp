import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name, stream_response


@click.command(help="Push local data to remote server")
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
