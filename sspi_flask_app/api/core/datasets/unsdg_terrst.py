from sspi_flask_app.api.datasource.sdg import collectSDGIndicatorData

def collect_unfao_terrst(**kwargs):
    yield from collectSDGIndicatorData(
        "15.1.2", "BIODIV", Metadata="TERRST,FRSHWT", **kwargs
    )
