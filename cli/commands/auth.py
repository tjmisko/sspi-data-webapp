import click
import json
from connector import SSPIDatabaseConnector


@click.group(help="Authentication and user management commands")
def auth():
    pass


@auth.command(help="Query all users in the authorization database")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def query(remote=False):
    connector = SSPIDatabaseConnector()
    res = connector.call("/auth/query", remote=remote)
    if res.status_code == 200:
        click.echo(res.text)
    else:
        click.secho(f"Error {res.status_code}: {res.text}", fg='red')


@auth.command(help="Get your current API token")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def token(remote=False):
    connector = SSPIDatabaseConnector()
    res = connector.call("/auth/token", remote=remote)
    if res.status_code == 200:
        click.echo(res.text)
    else:
        click.secho(f"Error {res.status_code}: {res.text}", fg='red')


@auth.command(help="Clear all users from the authorization database (DEBUG mode only)")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.confirmation_option(prompt="Are you sure you want to clear all users?")
def clear(remote=False):
    connector = SSPIDatabaseConnector()
    res = connector.call("/auth/clear", remote=remote)
    if res.status_code == 200:
        click.secho("All users cleared successfully", fg='green')
    else:
        click.secho(f"Error {res.status_code}: {res.text}", fg='red')