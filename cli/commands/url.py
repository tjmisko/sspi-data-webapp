import click
from connector import SSPIDatabaseConnector
import json


@click.command(help="Hit a URL stub")
@click.argument("url_stub", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def url(url_stub, remote=False):
    connector = SSPIDatabaseConnector()
    request_string = url_stub
    res = connector.call(request_string, remote=remote)
    click.echo(json.dumps(res.json()))
