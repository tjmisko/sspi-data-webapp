from flask import Blueprint, Response, jsonify, render_template, request
import logging
from flask_login import current_user, login_required

from sspi_flask_app.api.core.datasets import (
    dataset_cleaner_registry,
    dataset_collector_registry,
)
from sspi_flask_app.api.resources.utilities import (
    check_raw_document_set_coverage,
    parse_json,
    reduce_dataset_list,
)
from sspi_flask_app.models.database import sspi_metadata, sspi_raw_api_data

log = logging.getLogger(__name__)

dataset_bp = Blueprint(
    "dataset_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@dataset_bp.route("/collect/<series_code>", methods=["GET", "POST"])
@login_required
def collect(series_code: str):
    """
    Collect fetches data from external sources by series code
    and stores it in the database. It can handle both datasets and items.

    GET requests will return a collection form specifying which datasets
    are to be collected.

    POST requests will start the collection process and return a stream of
    collection progress updates. By default, POST requests will will collect
    only uncollected datasets. If the `overwriteAll` parameter is set to True,
    all datasets will be collected, even if they have already been collected.
    If `overwrite` parameters are provided at the dataset level, the 
    specified datasets will be collected and overwritten in addition to the 
    uncollected data.

    :param series_code: A SeriesCode may be either a DatasetCode or an ItemCode
    ---
    :url_param cli: If True, the function will return CLI-friendly info instead of rendering a template
    :url_param overwrite_all: If True, the function will overwrite existing data
    :url_param overwrite: A list of dataset codes to overwrite
    """
    cli = request.args.get("cli", False, type=bool)
    overwrite_all = request.args.get("overwriteAll", False)
    overwrite = request.args.getlist("overwrite")
    dataset_list = sspi_metadata.get_dataset_dependencies(series_code)
    username = current_user.username if current_user.is_authenticated else "Anonymous"
    if request.method == "POST":
        if overwrite_all:
            return Response(collect_iterator(dataset_list, username=username), mimetype="text/event-stream")
        uncollected_datasets, collected_datasets = check_raw_document_set_coverage(dataset_list)
        if overwrite:
            iterator_dataset_list = uncollected_datasets + [ds for ds in collected_datasets if ds in overwrite]
            return Response(collect_iterator(iterator_dataset_list, username=username), mimetype="text/event-stream")
        else:   
            return Response(collect_iterator(uncollected_datasets, username=username), mimetype="text/event-stream")
    uncollected_datasets, collected_datasets = check_raw_document_set_coverage(dataset_list)
    previous_collection_info = {}
    for ds in dataset_list:
        source_info = sspi_metadata.get_source_info(ds)  # Ensure source info is loaded for all datasets
        previous_collection_info[ds] = {
            "Source": source_info,
            "PreviouslyCollected": ds in collected_datasets,
            "CollectionInfo": sspi_raw_api_data.get_collection_info(source_info)
        }
    if not cli:
        return Response(render_template(
            "collect-confirmation-form.html",
            series_code=series_code,
            uncollected_datasets=uncollected_datasets,
            collected_datasets=collected_datasets,
            previous_collection_info=previous_collection_info,
        ))
    else:
        return jsonify({
            "uncollected_datasets": uncollected_datasets,
            "collected_datasets": collected_datasets,
            "previous_collection_info": previous_collection_info,
        })

def collect_iterator(dataset_list, **kwargs):
    """
    Generate the collect iterator for the dataset list 
    """
    reduced_dataset_list = reduce_dataset_list(dataset_list)
    log.info(reduced_dataset_list)
    for ds in reduced_dataset_list:
        source_info = sspi_metadata.get_source_info(ds)
        if sspi_raw_api_data.raw_data_available(source_info):
            sspi_raw_api_data.delete_many(
                sspi_raw_api_data.build_source_query(source_info)
            )
    for ds in reduced_dataset_list:
        collector = dataset_collector_registry.get(ds)
        if not collector:
            yield f"error: No collector implemented for dataset {ds}!\n"
        else:
            yield from collector(**kwargs)


@dataset_bp.route("/clean/<series_code>", methods=["GET"])        
@login_required
def clean_series_code(series_code: str):
    dataset_list = sspi_metadata.get_dataset_dependencies(series_code)
    if len(dataset_list) == 1:
        cleaner = dataset_cleaner_registry.get(dataset_list[0])
        if not cleaner:
            return jsonify({"error": f"No cleaner implemented for dataset {dataset_list[0]}!"}), 400
        else:
            return parse_json(cleaner())
    return Response(clean_iterator(dataset_list), mimetype="text/event-stream")

def clean_iterator(dataset_list):
    for i, ds in enumerate(dataset_list):
        cleaner = dataset_cleaner_registry.get(ds, None)
        if not cleaner:
            yield f"error: No cleaner implemented for dataset {ds}!\n"
        else:
            yield f"Cleaning dataset {ds} ( {i +1} of {len(dataset_list)} )\n"
            cleaner()
