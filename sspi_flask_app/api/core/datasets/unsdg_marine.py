from sspi_flask_app.api.datasource.sdg import collectSDGIndicatorData

def collect_unfao_marine(**kwargs):
    yield from collectSDGIndicatorData(
        "14.5.1", "BIODIV", IntermediateCode="MARINE", **kwargs
    )
