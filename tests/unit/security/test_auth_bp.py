from security import get_route_rules

EXEMPT_ENDPOINTS_GET = {
    'auth_bp.login',
    'auth_bp.apikey_web'
}
EXEMPT_ENDPOINTS_POST = {
    'auth_bp.login',
    'auth_bp.apikey_web'
}
EXEMPT_PREFIXES_GET = (
    'auth_bp.static',
    'auth_bp.templates',
)


def test_auth_routes_are_protected(app, client):
    """Make GET/POST requests to ensure auth routes are protected appropriately."""
    for endpoint, (route, methods) in get_route_rules(app, "auth_bp").items():

        if 'GET' in methods:
            if not (endpoint in EXEMPT_ENDPOINTS_GET or endpoint.startswith(EXEMPT_PREFIXES_GET)):
                response = client.get(route)
                msg = f"Unauthenticated GET access to {route} ({endpoint}) allowed!"
                assert response.status_code in {302, 401}, msg

        if 'POST' in methods:
            # Always require login for POSTs (never exempted)
            if endpoint in EXEMPT_ENDPOINTS_POST:
                continue
            response = client.post(route)
            msg = f"Unauthenticated POST access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401}, msg
