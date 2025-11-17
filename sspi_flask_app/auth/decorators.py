from functools import wraps
from flask import request, jsonify
from flask_login import login_required, current_user


def user_login_required(f):
    """
    Custom decorator that combines @login_required with automatic user_id injection.

    This decorator:
    1. Ensures the user is authenticated via Flask-Login
    2. Automatically injects current_user.username as user_id into request context
    3. Prevents user_id spoofing by validating any provided user_id matches the authenticated user
    4. Works for both GET (query params) and POST/PUT/DELETE/PATCH (JSON payload)

    Security Benefits:
    - Users cannot access or modify other users' data
    - Centralized authentication and authorization logic
    - Prevents user_id parameter tampering

    Usage:
        @customize_bp.route("/save", methods=["POST"])
        @user_login_required
        def save_configuration():
            user_id = request.user_id  # Automatically injected by decorator
            # ... use user_id safely knowing it's authenticated

    The decorator automatically:
    - Checks if user is logged in (redirects to login if not)
    - Injects authenticated user's username as request.user_id
    - Validates any provided user_id matches authenticated user (403 if mismatch)
    """
    @wraps(f)
    @login_required  # First, ensure user is logged in via Flask-Login
    def decorated_function(*args, **kwargs):
        # Get the authenticated user's username from Flask-Login's current_user
        user_id = current_user.username

        # Inject user_id into request context for easy access in route handlers
        request.user_id = user_id

        # For GET requests, verify user_id in query params matches authenticated user
        if request.method == 'GET':
            provided_user_id = request.args.get('user_id')
            if provided_user_id and provided_user_id != user_id:
                return jsonify({
                    "error": "Unauthorized: user_id mismatch",
                    "message": f"You can only access your own configurations. Expected user_id '{user_id}' but got '{provided_user_id}'"
                }), 403

        # For POST/PUT/DELETE/PATCH, verify user_id in JSON matches authenticated user
        elif request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if request.is_json:
                data = request.get_json(silent=True)
                if data and 'user_id' in data:
                    provided_user_id = data['user_id']
                    if provided_user_id != user_id:
                        return jsonify({
                            "error": "Unauthorized: user_id mismatch",
                            "message": f"You can only modify your own configurations. Expected user_id '{user_id}' but got '{provided_user_id}'"
                        }), 403

        # Call the original function with the injected user_id
        return f(*args, **kwargs)

    return decorated_function


def role_required(*required_roles):
    """
    Decorator to restrict access to users with specific roles.

    Args:
        *required_roles: One or more role names (e.g., "admin", "user")
                        User must have at least ONE of the specified roles

    Usage:
        @role_required("admin")
        def admin_only_route():
            ...

        @role_required("admin", "moderator")
        def admin_or_moderator_route():
            ...

    Returns:
        403 Forbidden if user lacks required role
    """
    def decorator(f):
        @wraps(f)
        @login_required  # Ensure user is authenticated first
        def decorated_function(*args, **kwargs):
            # Check if user has at least one of the required roles
            user_has_role = any(current_user.has_role(role) for role in required_roles)

            if not user_has_role:
                roles_str = ", ".join(required_roles)
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Access denied. Required role(s): {roles_str}"
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict access to admin users only.

    Shorthand for @role_required("admin")

    Usage:
        @admin_required
        def admin_only_route():
            ...

    Returns:
        403 Forbidden if user is not an admin
    """
    @wraps(f)
    @role_required("admin")
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


def owner_or_admin_required(f):
    """
    Decorator for routes that require ownership OR admin privileges.

    This decorator:
    1. Ensures the user is authenticated via Flask-Login
    2. Injects request.user_id from current_user.username
    3. Injects request.is_admin from current_user.is_admin()
    4. For routes with config_id: validates user owns config OR is admin
    5. Prevents user_id spoofing (validates provided user_id matches authenticated user)

    Security Model:
    - Regular users can only access their own data (ownership check)
    - Admins can access any user's data (admin bypass)
    - User_id parameter tampering is prevented

    Usage:
        @customize_bp.route("/load/<config_id>", methods=["GET"])
        @owner_or_admin_required
        def load_configuration(config_id):
            user_id = request.user_id    # Authenticated user's username
            is_admin = request.is_admin  # True if user is admin
            # Admin can load any config, regular user only their own
            ...

    The decorator automatically:
    - Checks if user is logged in
    - Injects request.user_id (authenticated user's username)
    - Injects request.is_admin (True if admin, False otherwise)
    - Validates any provided user_id matches authenticated user (403 if mismatch, unless admin)
    """
    @wraps(f)
    @login_required  # First, ensure user is logged in
    def decorated_function(*args, **kwargs):
        # Get authenticated user info
        user_id = current_user.username
        is_admin = current_user.is_admin()

        # Inject into request context
        request.user_id = user_id
        request.is_admin = is_admin

        # For GET requests, verify user_id in query params
        if request.method == 'GET':
            provided_user_id = request.args.get('user_id')
            if provided_user_id and provided_user_id != user_id:
                # Admins can access other users' data
                if not is_admin:
                    return jsonify({
                        "error": "Unauthorized: user_id mismatch",
                        "message": f"You can only access your own configurations. Expected user_id '{user_id}' but got '{provided_user_id}'"
                    }), 403

        # For POST/PUT/DELETE/PATCH, verify user_id in JSON
        elif request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if request.is_json:
                data = request.get_json(silent=True)
                if data and 'user_id' in data:
                    provided_user_id = data['user_id']
                    if provided_user_id != user_id:
                        # Admins can modify other users' data
                        if not is_admin:
                            return jsonify({
                                "error": "Unauthorized: user_id mismatch",
                                "message": f"You can only modify your own configurations. Expected user_id '{user_id}' but got '{provided_user_id}'"
                            }), 403

        # Call the original function with injected context
        return f(*args, **kwargs)

    return decorated_function
