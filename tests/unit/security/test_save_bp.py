from security import get_route_rules

EXEMPT_PREFIXES_GET = (
    'api_bp.save_bp.static',
)


def test_save_routes_are_protected(app, client):
    """Make GET/POST requests to ensure save routes are protected appropriately."""
    for endpoint, (route, methods) in get_route_rules(app, "api_bp.save_bp").items():

        if 'GET' in methods and not endpoint.startswith(EXEMPT_PREFIXES_GET):
            response = client.get(route)
            msg = f"Unauthenticated GET access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401}, msg

        if 'POST' in methods:
            response = client.post(route)
            msg = f"Unauthenticated POST access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401, 405}, msg

        if 'DELETE' in methods:
            # Always require login for DELETEs (never exempted)
            response = client.post(route)
            msg = f"Unauthenticated POST access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401, 405}, msg
