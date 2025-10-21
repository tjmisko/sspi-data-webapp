import click
from connector import SSPIDatabaseConnector
from cli.utilities import open_browser_subprocess


class DefaultGroup(click.Group):
    def resolve_command(self, ctx, args):
        try:
            # normal dispatch — works for “repo”, “project”, etc.
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # unknown token → treat it as an IDCODE and fall back
            idcode = args[0]
            if len(args) == 1 and len(idcode) == 6:
                return (
                    'line',
                    self.get_command(ctx, 'line'),
                    args
                )
            # anything else really is an error
            raise click.UsageError("Invalid command or IDCODE")


@click.group(cls=DefaultGroup, invoke_without_command=True, help="View webpages")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.pass_context
def view(ctx, remote=False):
    if ctx.invoked_subcommand is None:
        connector = SSPIDatabaseConnector()
        url = connector.remote_base if remote else connector.local_base
        open_browser_subprocess(url)


@view.command(help="View line chart")
@click.argument("idcode", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def line(idcode, remote=False):
    """
    Open a LINE chart plotting IDCODE by Year

    IDCODE is the IndicatorCode, IntermediateCode, PillarCode, CategoryCode,
    PillarCode, or CountryCode for the chart
    """
    connector = SSPIDatabaseConnector()
    base_url = connector.remote_base if remote else connector.local_base
    url = base_url + "/data/indicator/" + idcode
    open_browser_subprocess(url)


@view.command(help="View line chart")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def overview(remote=False):
    """Open DATA OVERVIEW chart
    """
    connector = SSPIDatabaseConnector()
    base_url = connector.remote_base if remote else connector.local_base
    url = base_url + "/data/overview"
    open_browser_subprocess(url)


@view.command(help="View GitHub Project")
def project():
    """Open GitHub Project in browser
    """
    url = "https://github.com/users/tjmisko/projects/4/views/1"
    open_browser_subprocess(url)


@view.command(help="View 2018 Paper")
def paper():
    """Open working paper page in browser
    """
    url = "https://irle.berkeley.edu/publications/working-papers/national-policies-to-support-sustainable-equitable-economies/"
    open_browser_subprocess(url)


@view.command(help="View Indicator Details")
def details():
    """Open GitHub Project in browser
    """
    url = "https://docs.google.com/spreadsheets/d/1nL0BwtKFvb7SXjPyMlbYCWyGtzQrRXRl_gM05-9ghGI/edit?gid=0#gid=0"
    open_browser_subprocess(url)


@view.command(help="View GitHub Repo")
def repo():
    """Open GitHub Project in browser
    """
    url = "https://github.com/tjmisko/sspi-data-webapp"
    open_browser_subprocess(url)


@view.command(help="View GitHub Repo")
def wiki():
    """Open GitHub Project in browser
    """
    url = "https://github.com/tjmisko/sspi-data-webapp/wiki"
    open_browser_subprocess(url)




view.add_command(line)
