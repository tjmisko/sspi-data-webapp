import click
import json
import secrets
import re
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
    if res.status_code != 200:
        click.secho(f"Error {res.status_code}: {res.text}", fg='red')
    click.echo(json.dumps(res.json()))


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


@auth.command(help="Register a new user (local only)")
def register():
    """
    Register a new user directly in the local database.
    This bypasses web interface protections for bootstrapping new installations.
    """
    from sspi_flask_app import flask_bcrypt
    from sspi_flask_app.models.usermodel import User
    from sspi_flask_app.models.errors import InvalidDocumentFormatError
    
    # Prompt for username (6-20 chars per RegisterForm)
    username = click.prompt("Username (6-20 characters)")
    
    # Validate username length (matching RegisterForm validators)
    if not (6 <= len(username) <= 20):
        click.secho("Error: Username must be 6-20 characters", fg='red')
        return
    
    # Check if username already exists
    if User.username_exists(username):
        click.secho("Error: Username already exists", fg='red')
        return
    
    # Password regex from RegisterForm - exact match
    password_regex = r'^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[\-!@#$%^&*()_+])[A-Za-z\d!\-@#$%^&*()_+]+$'
    
    # Prompt for password (hidden, twice for confirmation)
    password = click.prompt("Password (8-32 characters)", hide_input=True)
    confirm = click.prompt("Confirm password", hide_input=True)
    
    # Validate passwords match
    if password != confirm:
        click.secho("Error: Passwords do not match", fg='red')
        return
    
    # Validate password length (matching RegisterForm validators)
    if not (8 <= len(password) <= 32):
        click.secho("Error: Password must be 8-32 characters", fg='red')
        return
        
    # Validate password complexity (matching RegisterForm regex)
    if not re.match(password_regex, password):
        click.secho("Error: Password must contain at least one lowercase letter, "
                   "one uppercase letter, one digit, and one special character", fg='red')
        return
    
    # Generate hash exactly like register route
    hashed_password = flask_bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Create user with same key generation as register route
    try:
        user = User.create_user(
            username=username,
            password_hash=hashed_password,
            api_key=secrets.token_hex(64),  # 128-char hex string
            secret_key=secrets.token_hex(32)  # 64-char hex string
        )
        click.secho(f"\n✓ User '{username}' created successfully!", fg='green')
        click.echo(f"API Key: {user.apikey}")
        click.echo("\nYou can now log in via the web interface or use the API key for authentication.")
    except InvalidDocumentFormatError as e:
        click.secho(f"Error: {str(e)}", fg='red')
    except Exception as e:
        click.secho(f"Error creating user: {str(e)}", fg='red')
