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
    
    # Check content type to determine how to handle response
    content_type = res.headers.get('content-type', '').lower()
    
    if 'application/json' in content_type:
        # JSON response - parse and pretty print
        try:
            click.echo(json.dumps(res.json()))
        except json.JSONDecodeError:
            click.echo(f"Error: Failed to parse JSON response\nStatus: {res.status_code}\nContent: {res.text}")
    elif 'text/html' in content_type:
        # HTML response - just return status and first few lines
        click.echo(f"HTML Response (Status: {res.status_code})")
        click.echo(f"Content-Type: {res.headers.get('content-type')}")
        lines = res.text.split('\n')[:5]
        click.echo("First few lines:")
        for line in lines:
            click.echo(f"  {line.strip()}")
    else:
        # Other content types - show basic info
        click.echo(f"Response (Status: {res.status_code})")
        click.echo(f"Content-Type: {res.headers.get('content-type')}")
        click.echo(f"Content Length: {len(res.text)}")
        if len(res.text) < 500:
            click.echo(f"Content: {res.text}")
