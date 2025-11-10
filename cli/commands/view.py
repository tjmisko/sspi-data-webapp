import click
from connector import SSPIDatabaseConnector
from cli.utilities import open_browser_subprocess


@click.group(help="View webpages")
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.pass_context
def view(ctx, remote=False):
    if ctx.invoked_subcommand is None:
        connector = SSPIDatabaseConnector()
        url = connector.remote_base if remote else connector.local_base
        open_browser_subprocess(url)


@view.command(help="View line chart")
@click.argument("series_code", type=str, required=True)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
def line(series_code, remote=False):
    """
    Open a LINE chart plotting SERIES_CODE by Year
    SERIES_CODE is the IndicatorCode, DatasetCode, PillarCode, CategoryCode,
    PillarCode for the chart
    """
    series_code = series_code.upper()
    connector = SSPIDatabaseConnector()
    res = connector.call(f"/api/v1/query/metadata/series_detail/{series_code}", remote=remote)
    res.raise_for_status()
    item_detail = res.json()
    item_type = item_detail.get("ItemType", "")
    base_url = connector.remote_base if remote else connector.local_base
    if item_type == "Dataset":
        url = base_url + "/data/dataset/" + series_code 
    elif item_type == "Indicator":
        url = base_url + "/data/indicator/" + series_code 
    elif item_type == "Category":
        url = base_url + "/data/category/" + series_code 
    elif item_type == "Pillar":
        url = base_url + "/data/pillar/" + series_code 
    else:
        return f"Series {series_code} not found in SSPI Metadata."
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
