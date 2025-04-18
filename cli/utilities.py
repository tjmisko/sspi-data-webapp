import subprocess
from os import environ, path
from dotenv import load_dotenv
import re
import click


def full_name(name):
    if name == "raw":
        return "sspi_raw_api_data"
    if name == "meta" or name == "metadata":
        return "sspi_metadata"
    if name == "clean":
        return "sspi_clean_api_data"
    return name


def is_numeric_string(string):
    pattern = r"^[0-9,.]+$"
    return bool(re.match(pattern, string))


def echo_pretty(msg):
    tokens = msg.split(" ")
    output = []
    for i, t in enumerate(tokens):
        if is_numeric_string(t):
            output.append(click.style(t, fg='cyan'))
        else:
            output.append(t)
    click.echo(" ".join(output))


def require_confirmation(phrase="CONFIRM", prompt="Type {0} to confirm") -> bool:
    prompt_string = prompt.format(click.style(phrase, fg="red"))
    confirmation = click.prompt(prompt_string, default="", show_default=False)
    if confirmation != phrase:
        click.secho("Confirmation failed. Exiting.", fg="red")
        return False
    click.secho("Confirmation successful!", fg="green")
    return True


def open_browser_subprocess(url):
    """Opens a subprocess for rendering charts using the browser.
    Browser and behavior can be customized by setting SSPI_VIEW_COMMAND
    .env. A suggested configuration is `firefox --kiosk --new-window`
    """
    basedir = path.abspath(path.dirname(path.dirname(__file__)))
    load_dotenv(path.join(basedir, '.env'))
    view_cmd = environ.get('SSPI_VIEW_COMMAND')
    subprocess.Popen(
        view_cmd.split(" ") + [url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )
