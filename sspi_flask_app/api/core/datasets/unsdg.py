from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data
from sspi_flask_app.api.core.datasets import dataset

@dataset("UNSDG_FRSHWT")
def collect_unsdg_frshwt(**kwargs):
    yield from collect_sdg_indicator_data("15.1.2", **kwargs)


@dataset("UNSDG_MARINE")
def collect_unsdg_marine(**kwargs):
    yield from collect_sdg_indicator_data("14.5.1", **kwargs)


@dataset("UNSDG_TERRST")
def collect_unsdg_terrst(**kwargs):
    yield from collect_sdg_indicator_data("15.1.2", **kwargs)
