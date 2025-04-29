from security import get_route_rules

EXEMPT_PREFIXES_GET = (
    'api_bp.finalize_bp.static',

    'api_bp.finalize_bp.templates',
)


def test_finalize_routes_are_protected(app, client):
    """Make GET requests to ensure finalize routes are protected appropriately."""
    for endpoint, (route, methods) in get_route_rules(app, "api_bp.finalize_bp").items():
        app.logger.debug(f"Testing endpoint: {endpoint}")
        if 'GET' in methods and not endpoint.startswith(EXEMPT_PREFIXES_GET):
            response = client.get(route)
            msg = f"Unauthenticated GET access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401}, msg
