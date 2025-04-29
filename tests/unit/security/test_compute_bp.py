from security import get_route_rules

EXEMPT_PREFIXES_GET = (
    'api_bp.compute_bp.static',
    'api_bp.compute_bp.templates',
)


def test_compute_routes_are_protected(app, client):
    """Make GET requests to ensure compute routes are protected appropriately."""
    for endpoint, (route, methods) in get_route_rules(app, "api_bp.compute_bp").items():
        if 'GET' in methods and not endpoint.startswith(EXEMPT_PREFIXES_GET):
            response = client.get(route)
            msg = f"Unauthenticated GET access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401}, msg
