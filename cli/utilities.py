import subprocess
from os import environ, path
from dotenv import load_dotenv
import re
import click
import sys


def full_name(name):
    if name == "raw":
        return "sspi_raw_api_data"
    if name == "meta" or name == "metadata":
        return "sspi_metadata"
    if name == "clean":
        return "sspi_clean_api_data"
    if name == "incomplete":
        return "sspi_incomplete_api_data"
    if name == "imputed":
        return "sspi_imputed_data"
    return name


def is_numeric_string(string):
    pattern = r"^[0-9,.]+$"
    return bool(re.match(pattern, string))


def echo_pretty(msg):
    if type(msg) is bytes:
        msg = msg.decode("utf-8")
    lines = msg.splitlines()
    for line in lines:
        if "error:" in line[0:8] or "problem:" in line[0:9]:
            click.secho(line.split(": ", 1)[1], fg='red')
            continue
        tokens = re.split(r"([\[\],()\s]+)", line)
        output = []
        for i, t in enumerate(tokens):
            if is_numeric_string(t):
                output.append(click.style(t, fg='cyan'))
            else:
                output.append(t)
        click.echo("".join(output))


def require_confirmation(phrase="CONFIRM", prompt="Type {0} to confirm") -> bool:
    prompt_string = prompt.format(click.style(phrase, fg="red"))
    confirmation = click.prompt(prompt_string, default="", show_default=False)
    if confirmation != phrase:
        click.secho("\nConfirmation failed. Exiting.", fg="red")
        return False
    click.secho("\nConfirmation successful!\n", fg="green")
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


def stream_response(res):
    exit_code = 0
    with res as event_stream:
        for line in event_stream.iter_lines(decode_unicode=True):
            if type(line) is bytes:
                line = line.decode("utf-8")
            echo_pretty(line)
            if "error:" in line:
                exit_code = 1
    return exit_code


def stdin_is_empty():
    return sys.stdin.isatty()
