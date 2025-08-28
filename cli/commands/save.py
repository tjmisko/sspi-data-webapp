import click
from connector import SSPIDatabaseConnector
from cli.utilities import full_name, stream_response, echo_pretty


@click.command(help="Finalize clean data for plotting")
@click.argument("database", type=str, required=False)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def save(database, remote=False):
    if not database:
        connector = SSPIDatabaseConnector()
        url = "/api/v1/save"
        stream_response(connector.call(url, remote=remote, stream=True))
    else:
        database = full_name(database)
        connector = SSPIDatabaseConnector()
        url = f"/api/v1/save/{database}"
        res = connector.call(url, remote=remote)
        echo_pretty(res.text)
