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
