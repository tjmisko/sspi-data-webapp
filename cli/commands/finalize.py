import click
from connector import SSPIDatabaseConnector
from cli.utilities import stream_response


@click.group(invoke_without_command=True, help="Finalize clean data for plotting")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.pass_context
def finalize(ctx, remote=False):
    if ctx.invoked_subcommand is None:
        connector = SSPIDatabaseConnector()
        url = "/api/v1/production/finalize"
        stream_response(connector.call(url, remote=remote, stream=True))


@finalize.group(help="Finalize dynamic data")
def dynamic():
    pass


@finalize.command(help="Finalize indicator dynamic line data")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def line(remote=False):
    click.echo("Finalizing Dynamic Line Data")
    connector = SSPIDatabaseConnector()
    url = "/api/v1/production/finalize/dynamic/line"
    stream_response(connector.call(url, remote=remote, stream=True))
    click.secho("\nFinalization Complete", fg="green")


@finalize.command(help="Finalize indicator dynamic matrix data")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def overview(remote=False):
    click.echo("Finalizing Dynamic Line Data")
    connector = SSPIDatabaseConnector()
    url = "/api/v1/production/finalize/dynamic/matrix"
    stream_response(connector.call(url, remote=remote, stream=True))
    click.secho("\nFinalization Complete", fg="green")


@finalize.command(help="Finalize dynamic score data")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--country", "-c", multiple=True, help="Country codes to finalize")
@click.option("--country-group", "-g", default="SSPI67", help="Country group code to finalize")
def score(remote=False, country=[], country_group="SSPI67"):
    click.echo("Finalizing Dynamic Score Data")
    connector = SSPIDatabaseConnector()
    url = "/api/v1/production/finalize/dynamic/score"
    if country or country_group:
        url += "?"
    if country_group:
        url += f"CountryGroup={country_group}&"
    if country:
        url += "".join(["CountryCode={c}&".format(c=c) for c in country])
    url = url.rstrip("&")
    stream_response(connector.call(url, remote=remote, stream=True))
    click.secho("\nFinalization Complete", fg="green")


dynamic.add_command(score)
dynamic.add_command(overview)
dynamic.add_command(line)
finalize.add_command(dynamic)
