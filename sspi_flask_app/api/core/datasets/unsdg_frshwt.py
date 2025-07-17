from sspi_flask_app.api.datasource.sdg import collectSDGIndicatorData

def collect_unfao_frshwt(**kwargs):
    yield from collectSDGIndicatorData(
        "15.1.2", "BIODIV", Metadata="FRSHWT", **kwargs
    )

