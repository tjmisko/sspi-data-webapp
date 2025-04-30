import click
from connector import SSPIDatabaseConnector
from cli.utilities import stream_response


@click.command(help="Collect raw data from source APIs")
@click.argument("indicator_code", type=str)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def collect(indicator_code, remote=False):
    connector = SSPIDatabaseConnector()
    indicator_code = indicator_code.upper()
    request_string = f"/api/v1/collect/{indicator_code}"
    stream_response(connector.call(request_string, remote=remote, stream=True))
