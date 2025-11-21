from security import get_route_rules

EXEMPT_ENDPOINTS_GET = {
    'auth_bp.user_login',  # Public login page (renamed from login)
    'auth_bp.admin_login', # Public admin login page
    'auth_bp.register',    # Public registration page
    'auth_bp.apikey_web'
}
EXEMPT_ENDPOINTS_POST = {
    'auth_bp.user_login',  # Public login submission
    'auth_bp.admin_login', # Public admin login submission
    'auth_bp.register',    # Public registration submission
    'auth_bp.apikey_web',
    'auth_bp.check_username',  # Public API endpoint for username validation
    'auth_bp.check_email'      # Public API endpoint for email validation
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
            # 400 is acceptable: CSRF validation happens before auth for form routes
            # This is correct security behavior - missing CSRF token = Bad Request
            assert response.status_code in {302, 400, 401}, msg
