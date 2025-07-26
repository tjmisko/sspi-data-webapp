from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner

@dataset_collector("UNSDG_MARINE")
def collect_unsdg_marine(**kwargs):
    yield from collect_sdg_indicator_data("14.5.1", **kwargs)
