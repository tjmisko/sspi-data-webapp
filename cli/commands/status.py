import click
from connector import SSPIDatabaseConnector
import json


@click.command(help="Show connector status and target URLs")
def status():
    connector = SSPIDatabaseConnector()
    
    status_info = {
        "local_url": connector.local_base,
        "remote_url": connector.remote_base,
        "local_port": connector.local_port_number
    }
    
    click.echo(json.dumps(status_info, indent=2))