import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name, echo_pretty


@click.command(help="Pull local data to remote server")
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
