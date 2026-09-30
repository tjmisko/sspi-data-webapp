import re

import pytest

from security import get_route_rules

# A syntactically valid Bearer header that matches no user. It passes the
# blueprint's require_bearer_for_writes prefix check, so only the route's own
# @admin_required decorator stands between the request and the handler.
UNKNOWN_BEARER_HEADERS = {"Authorization": "Bearer not-a-real-api-key"}

WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def concrete_route(route):
    """Fill URL converters like <series_code> so the rule can be requested."""
    return re.sub(r"<[^>]+>", "SSPI", route)


def write_routes(app, blueprint_name):
    return [
        (endpoint, concrete_route(route), method)
        for endpoint, (route, methods) in get_route_rules(app, blueprint_name).items()
        for method in WRITE_METHODS
        if method in methods
    ]


@pytest.mark.parametrize("blueprint_name", ["api_bp.compute_bp", "api_bp.impute_bp"])
def test_write_routes_should_return_401_when_bearer_key_matches_no_user(app, client, blueprint_name):
    routes = write_routes(app, blueprint_name)
    assert routes, f"No write routes discovered on {blueprint_name}"
    unprotected = []
    for endpoint, route, method in routes:
        response = client.open(route, method=method, headers=UNKNOWN_BEARER_HEADERS)
        if response.status_code != 401:
            unprotected.append(f"{method} {route} ({endpoint}) -> {response.status_code}")
    assert not unprotected, "Write routes reachable without a valid admin key:\n" + "\n".join(unprotected)


@pytest.mark.parametrize("blueprint_name", ["api_bp.compute_bp", "api_bp.impute_bp"])
def test_write_routes_should_return_403_when_authorization_header_is_missing(app, client, blueprint_name):
    for endpoint, route, method in write_routes(app, blueprint_name):
        response = client.open(route, method=method)
        msg = f"{method} {route} ({endpoint}) accepted a request with no Bearer header"
        assert response.status_code == 403, msg


def test_impute_routes_are_protected(app, client):
    """Make GET requests to ensure impute routes are protected appropriately."""
    for endpoint, (route, methods) in get_route_rules(app, "api_bp.impute_bp").items():
        if "GET" in methods and not endpoint.startswith(("api_bp.impute_bp.static", "api_bp.impute_bp.templates")):
            response = client.get(concrete_route(route))
            msg = f"Unauthenticated GET access to {route} ({endpoint}) allowed!"
            assert response.status_code in {302, 401, 404, 405}, msg
