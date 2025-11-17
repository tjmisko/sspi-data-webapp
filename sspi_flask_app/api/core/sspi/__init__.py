import time
from flask import Blueprint, current_app, Response, session
from flask_login import login_required, current_user, login_user
from sspi_flask_app.models.database import sspi_metadata
from sspi_flask_app.auth.decorators import admin_required

compute_bp = Blueprint(
    "compute_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/compute",
)

impute_bp = Blueprint(
    "impute_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/impute",
)

_COMPUTE_REGISTRY = {}
_IMPUTE_REGISTRY = {}
_REGISTRY_INITIALIZED = False


def _build_registries_via(app_like):
    """
    Discover all compute/impute endpoints automatically using endpoint names,
    which are stable regardless of nested blueprint URL prefixes.
    """
    print("Building Registries")
    global _REGISTRY_INITIALIZED
    if _REGISTRY_INITIALIZED:
        return
    for rule in app_like.url_map.iter_rules():
        endpoint = rule.endpoint
        fn = app_like.view_functions[endpoint]
        methods = rule.methods or set()
        # Skip non-POST routes
        if "POST" not in methods:
            continue
        # Extract the indicator code as the last path segment
        code = rule.rule.rsplit("/", 1)[-1]
        # Skip aggregator routes like /.../<series_code>
        if code.startswith("<") and code.endswith(">"):
            continue
        code = code.upper()
        print(rule)
        # Detect by endpoint prefix (blueprint name), not by URL prefix
        if endpoint.startswith("api_bp.compute_bp."):
            _COMPUTE_REGISTRY[code] = fn
        elif endpoint.startswith("api_bp.impute_bp."):
            print(code)
            _IMPUTE_REGISTRY[code] = fn
    _REGISTRY_INITIALIZED = True


def _call_internal(fn, path, make_ctx, user_obj, user_id):
    """
    Safely call another Flask route function:
      - use a fresh request context via the bound make_ctx
      - rehydrate authentication for @admin_required routes
    """
    with make_ctx(path, method="POST"):
        # Prefer logging in the captured user object; fall back to seeding session.
        try:
            if getattr(user_obj, "is_authenticated", False):
                login_user(user_obj)
            elif user_id is not None:
                # If your LoginManager reads _user_id from the session
                session["_user_id"] = user_id  # type: ignore[index]
        except Exception:
            # Don't let auth rehydration break the internal call
            pass
        return fn()


def call_compute(indicator_code, make_ctx, user_obj, user_id):
    fn = _COMPUTE_REGISTRY.get(indicator_code.upper())
    if fn is None:
        return None
    # The path only needs to be plausible; we call fn() directly.
    return _call_internal(fn, f"/compute/{indicator_code}", make_ctx, user_obj, user_id)


def call_impute(indicator_code, make_ctx, user_obj, user_id):
    fn = _IMPUTE_REGISTRY.get(indicator_code.upper())
    if fn is None:
        return None
    return _call_internal(fn, f"/impute/{indicator_code}", make_ctx, user_obj, user_id)


# ============================================================
#  ROUTES (refactored to use internal dispatcher)
# ============================================================

@compute_bp.route("/<series_code>", methods=["POST"])
@admin_required
def compute_series(series_code):
    # Build registries while request/app context is alive.
    _build_registries_via(current_app)
    # Capture bound context factory and user info BEFORE streaming.
    make_ctx = current_app.test_request_context  # bound to the real app instance
    # Resolve a concrete user object if available, otherwise use the proxy as-is.
    user_obj = getattr(current_user, "_get_current_object", lambda: current_user)()
    user_id = getattr(user_obj, "get_id", lambda: None)()
    def compute_iterator(series_code):
        target_series = "SSPI" if series_code.upper() == "ALL" else series_code
        indicator_codes = sspi_metadata.get_indicator_dependencies(target_series)
        for ic in indicator_codes:
            fn = _COMPUTE_REGISTRY.get(ic.upper())
            if fn is None:
                yield f"No compute route for {ic}\n"
                continue
            try:
                rv = call_compute(ic, make_ctx, user_obj, user_id)
                status = getattr(rv, "status_code", 200) if rv is not None else 404
                yield f"Compute {ic}: {status}\n"
            except Exception:
                yield f"Compute {ic} returned an error: {500}\n"
        yield "Computation Complete\n"
    return Response(compute_iterator(series_code), mimetype="text/event-stream")


@impute_bp.route("/<series_code>", methods=["POST"])
@admin_required
def impute_all(series_code):
    print("Registry State Initialized?", _REGISTRY_INITIALIZED)
    _build_registries_via(current_app)
    print(_IMPUTE_REGISTRY)
    make_ctx = current_app.test_request_context
    user_obj = getattr(current_user, "_get_current_object", lambda: current_user)()
    user_id = getattr(user_obj, "get_id", lambda: None)()
    def impute_iterator(series_code):
        target_series = "SSPI" if series_code.upper() == "ALL" else series_code
        indicator_codes = sspi_metadata.get_indicator_dependencies(target_series)
        for ic in indicator_codes:
            fn = _IMPUTE_REGISTRY.get(ic.upper())
            if fn is None:
                yield f"No Impute route for {ic}\n"
                continue
            try:
                rv = call_impute(ic, make_ctx, user_obj, user_id)
                status = getattr(rv, "status_code", 200) if rv is not None else 404
                yield f"Impute {ic}: {status}\n"
            except Exception:
                yield f"Impute {ic} returned an error: {500}\n"
        yield "Imputation Complete\n"
    return Response(impute_iterator(series_code), mimetype="text/event-stream")
