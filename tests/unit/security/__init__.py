def get_route_rules(app, blueprint_name):
    """Get a mapping of endpoint to (route, methods) for all registered routes."""
    return {
        rule.endpoint: (rule.rule, rule.methods)
        for rule in app.url_map.iter_rules()
        if rule.endpoint.startswith(blueprint_name + '.')
    }
