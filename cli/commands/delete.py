import click
from connector import SSPIDatabaseConnector
from cli.utilities import (
    full_name,
    echo_pretty,
    require_confirmation,
)


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
@click.option("--force", "-f", is_flag=True, help="DANGER: Override Confirmation")
def clear(database, remote=False, force=False):
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
    if force or require_confirmation(phrase=database, prompt="".join(prompt_lst)):
        url = f"/api/v1/delete/clear/{database}"
        res = connector.call(url, remote=remote, method="DELETE")
        echo_pretty(res.text)


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
