import secrets
from flask import (
    current_app as app,
    Blueprint,
    Response,
    jsonify,
    render_template,
    request,
    url_for,
    redirect,
    flash,
)
from sspi_flask_app.models.usermodel import User
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app.models.database import sspi_user_data
from sspi_flask_app import login_manager, flask_bcrypt

# from sqlalchemy_serializer import SerializerMixin
# from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    fresh_login_required,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Regexp
from urllib.parse import urljoin, urlparse


auth_bp = Blueprint(
    "auth_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/auth/static",
)

login_manager.login_view = "auth_bp.login"


@login_manager.user_loader
def load_user(user_id):
    app.logger.debug(f"User Loader: Loading user {user_id} from session")
    user = User.find_by_id(user_id)
    if not user:
        app.logger.warning(f"User Loader: User {user_id} not found in session")
        return None
    app.logger.info(f"User Loader: Found user {user.username} in session")
    return user


class UpdatePasswordForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
        label="Username",
    )
    oldpassword = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Old Password"},
        label="Old Password",
    )
    newpassword = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "New Password"},
        label="New Password",
    )
    newpasswordconfirm = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Confirm Password"},
        label="Confirm Password",
    )
    submit = SubmitField("Change Password")


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=6, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[
            InputRequired(),
            Length(min=8, max=32),
            Regexp(
                r"^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[\-!@#$%^&*()_+])[A-Za-z\d!\-@#$%^&*()_+]+$",
                message=(
                    "Password must contain at least one lowercase letter, "
                    "one uppercase letter, one digit, and one special character."
                ),
            ),
        ],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        # Check if username is already taken using MongoDB
        if User.username_exists(username.data):
            raise ValidationError("That username is already taken!")


class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
        label="Username",
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Password"},
        label="Password",
    )
    remember_me = BooleanField(default=False, label="Remember me for 30 days")
    submit = SubmitField("Login as Administrator")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next", None)
    if current_user.is_authenticated:
        return redirect(url_for("client_bp.data"))
    login_form = LoginForm()
    if not login_form.validate_on_submit():
        return render_template("login.html", form=login_form, title="Login")
    user = User.find_by_username(login_form.username.data)
    if user is None or not flask_bcrypt.check_password_hash(
        user.password, login_form.password.data
    ):
        flash("Invalid username or password")
        return render_template(
            "login.html",
            form=login_form,
            error="Invalid username or password",
            title="Login",
        )
    login_user(
        user,
        remember=bool(login_form.remember_me),
        duration=app.config["REMEMBER_COOKIE_DURATION"],
    )
    if not next_url:
        return redirect(url_for("client_bp.data"))
    if not is_safe_url(next_url):
        return Response("Invalid next URL", status=400, mimetype="text/plain")
    flash("Login Successful! Redirecting...")
    app.logger.info(f"User {user.username} successful login")
    return redirect(urljoin(request.host_url, next_url))


@auth_bp.route('/auth/key', methods=['GET', 'POST'])
def apikey_web():
    if current_user.is_authenticated:
        return Response(current_user.apikey, 200, mimetype='text/plain')
    form = LoginForm()
    if request.method == 'GET' or not form.validate_on_submit():
        return render_template('apikey.html',
                               form=form,
                               title="Retrieve API Key")
    user = User.find_by_username(form.username.data)
    if user is None or not flask_bcrypt.check_password_hash(
            user.password, form.password.data):
        flash("Invalid username or password")
        return render_template('apikey.html',
                               form=form,
                               error="Invalid username or password",
                               title="Retrieve API Key"), 405
    return Response(user.apikey, 200, mimetype='text/plain')


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    try:
        current_username = current_user.username
    except AttributeError:
        app.logger.warning("Anonymous user attempted to log out")
        return Response("Error retrieving current user username", status=500)
    app.logger.info(f"Processing logout request for {current_username}")
    logout_user()
    app.logger.info(f"User {current_username} logged out")
    return redirect(url_for("client_bp.home"))


@auth_bp.route("/register", methods=["GET", "POST"])
@fresh_login_required
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        try:
            hashed_password = flask_bcrypt.generate_password_hash(
                register_form.password.data
            ).decode('utf-8')
            User.create_user(
                username=register_form.username.data,
                password_hash=hashed_password,
                api_key=secrets.token_hex(64),
                secret_key=secrets.token_hex(32)
            )
            return redirect(url_for("auth_bp.login"))
        except InvalidDocumentFormatError as e:
            flash(f"Registration failed: {str(e)}")
    return render_template("register.html", form=register_form, title="Register")


@auth_bp.route("/auth/clear", methods=["GET"])
@fresh_login_required
def clear():
    if not app.config["DEBUG"]:
        return Response("This route is only available in DEBUG mode", status=403)
    sspi_user_data.delete_many({})  # Clear all users
    return redirect(url_for("auth_bp.login"))


@auth_bp.route("/auth/query", methods=["GET"])
@fresh_login_required
def query():
    users = User.get_all_users()
    user_info = []
    for user in users:
        user_info.append({
            'username': user.username,
            'apikey': user.apikey,
            'id': user.id
        })
    return str(user_info)


@auth_bp.route("/auth/token", methods=["GET"])
def token():
    # Check if user is authenticated via session
    if current_user.is_authenticated:
        return str(current_user.apikey)
    
    # Check for API token authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return Response("Unauthorized", status=401)
    
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return Response("Invalid Authorization header format", status=401)
    
    api_token = parts[1]
    app.logger.debug(f"Looking up API token: {api_token[:10]}...")
    user = User.find_by_api_key(api_token)
    if not user:
        app.logger.warning(f"No user found for API token: {api_token[:10]}...")
        return Response("Invalid API key", status=401)
    
    app.logger.info(f"Found user {user.username} for API token")
    return str(user.apikey)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@login_manager.unauthorized_handler
def unauthorized():
    return "Unauthorized to Access Requested Route", 401


@login_manager.request_loader
def load_user_from_request(request):
    app.logger.debug(f"request_loader fired for request {request}")
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        app.logger.warning("Invalid Authorization header format")
        return None
    api_token = parts[1]
    if not api_token:
        app.logger.warning("No API key provided!")
        return None
    user = User.find_by_api_key(api_token)
    if not user:
        app.logger.warning("No user associated with provided API key")
        return None
    app.logger.info(f"User {user.username} Loaded from API Key")
    return user
