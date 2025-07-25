import click
import json
from connector import SSPIDatabaseConnector
from cli.utilities import stream_response


@click.command(help="Collect raw data from source APIs")
@click.argument("series_code", type=str)
@click.option("--remote", "-r", is_flag=True, help="Send the request to the remote server")
@click.option("--overwrite-all", "-O", default=False, is_flag=True, help="Overwrite all existing data for the series")
@click.option("--overwrite", "-o", multiple=True, required=False, is_flag=True, help="")
def collect(series_code, overwrite_all: bool, overwrite: list[str], remote: bool):
    connector = SSPIDatabaseConnector()
    series_code = series_code.upper()
    request_string = f"/api/v1/collect/{series_code}?cli=true"
    if overwrite_all:
        request_string += "&overwriteAll=true"
        stream_response(connector.call(request_string, method="POST", remote=remote, stream=True))
    elif overwrite:
        for code in overwrite:
            request_string += f"&overwrite={code}"
        stream_response(connector.call(request_string, method="POST", remote=remote, stream=True))
    else:
        res = connector.call(request_string, remote=remote)
        data = res.json()
        uncollected_datasets = data.get("uncollected_datasets", [])
        collected_datasets = data.get("collected_datasets", [])
        previous_collection_info = data.get("previous_collection_info", {})
        if not collected_datasets:
            click.echo("Collecting RawDocumentSets for the following Datasets:")
            click.secho("\t" + ", ".join(uncollected_datasets), fg="yellow")
            stream_response(connector.call(request_string, method="POST", remote=remote, stream=True))
            return
        if uncollected_datasets:
            click.echo("RawDocumentSets for the following Datasets will be collected:")
            click.secho("\t" + ", ".join(uncollected_datasets), fg="yellow")
        overwrite_list = []
        if collected_datasets:
            for dataset in collected_datasets:
                click.echo(f"A RawDocumentSet for {dataset} has already been collected.")
                if dataset in previous_collection_info.keys():
                    click.echo("Previous collection info:")
                    click.secho(json.dumps(previous_collection_info[dataset]["CollectionInfo"], indent=2), fg="yellow")
                    click.echo("Source Info:")
                    click.secho(json.dumps(previous_collection_info[dataset]["Source"], indent=2), fg="yellow")
                if click.confirm("Do you want to overwrite the RawDocumentSet associated with this dataset?"):
                    overwrite_list.append(dataset)
        if overwrite_list:
            for dataset_code in overwrite_list:
                request_string += f"&overwrite={dataset_code}"
        click.secho(request_string, fg="blue")
        stream_response(connector.call(request_string, method="POST", remote=remote, stream=True))

