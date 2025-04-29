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
    flash
)
from sspi_flask_app.models.usermodel import User, db
from sspi_flask_app import login_manager, flask_bcrypt
# from sqlalchemy_serializer import SerializerMixin
# from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    fresh_login_required,
    login_user,
    login_required,
    logout_user,
    current_user
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Regexp
from urllib.parse import urljoin, urlparse


auth_bp = Blueprint(
    'auth_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/auth/static'
)

login_manager.login_view = "auth_bp.login"


@login_manager.user_loader
def load_user(user_id):
    app.logger.debug(f"User Loader: Loading user {user_id} from session")
    user = User.query.get(user_id)
    if not user:
        app.logger.warning(f"User Loader: User {user_id} not found in session")
        return None
    app.logger.info(f"User Loader: Found user {user.username} in session")
    return user


class UpdatePasswordForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"}, label="Username")
    oldpassword = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Old Password"}, label="Old Password")
    newpassword = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "New Password"}, label="New Password")
    newpasswordconfirm = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Confirm Password"}, label="Confirm Password")
    submit = SubmitField("Change Password")


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(min=6, max=20)
        ],
        render_kw={"placeholder": "Username"}
    )
    password = PasswordField(
        validators=[
            InputRequired(),
            Length(min=8, max=32),
            Regexp(
                r'^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[\-!@#$%^&*()_+])[A-Za-z\d!\-@#$%^&*()_+]+$',
                message=(
                    "Password must contain at least one lowercase letter, ",
                    "one uppercase letter, one digit, and one special character."
                )
            )
        ],
        render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        # query the database to check whether the submitted new username is taken
        username_taken = User.query.filter_by(username=username.data).first()
        # if the username is taken, raise a validation ValidationError
        if username_taken:
            raise ValidationError("That username is already taken!")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"}, label="Username")
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"}, label="Password")
    remember_me = BooleanField(default=False, label="Remember me for 30 days")
    submit = SubmitField("Login as Administrator")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next', None)
    if current_user.is_authenticated:
        return redirect(url_for('client_bp.data'))
    login_form = LoginForm()
    if not login_form.validate_on_submit():
        return render_template('login.html', form=login_form, title="Login")
    user = User.query.filter_by(username=login_form.username.data).first()
    if user is None or not flask_bcrypt.check_password_hash(user.password, login_form.password.data):
        flash("Invalid username or password")
        return render_template('login.html', form=login_form, error="Invalid username or password", title="Login")
    login_user(
        user,
        remember=login_form.remember_me,
        duration=app.config['REMEMBER_COOKIE_DURATION']
    )
    if not next_url:
        return redirect(url_for("client_bp.data"))
    if not is_safe_url(next_url):
        return Response("Invalid next URL", status=400, mimetype='text/plain')
    flash("Login Successful! Redirecting...")
    app.logger.info(f"User {user.username} successful login")
    return redirect(urljoin(request.host_url, next_url))


@auth_bp.route('/remote/session/login', methods=['POST'])
def remote_login():
    auth_header = request.headers.get('Authorization', None)
    if not auth_header or not auth_header.startswith('Bearer '):
        app.logger.warning("No API key provided or incorrect format!")
        return jsonify({"message": "No API key provided or incorrect format"}), 401
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != 'Bearer':
        return jsonify({"message": "Invalid Authorization header format"}), 401
    api_token = parts[1]
    if not api_token:
        app.logger.warning("No API key provided!")
        return jsonify({"message": "No API key provided"}), 401
    user = User.query.filter_by(apikey=api_token).first()
    if user is not None:
        login_user(user, remember=True,
                   duration=app.config['REMEMBER_COOKIE_DURATION'])
        app.logger.info(f"User {user.username} successful login")
        return "Remote Login Successful"
    app.logger.warning("Login attempt failed!")
    return jsonify({"message": "Invalid API key"}), 401


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    current_username = current_user.username
    app.logger.info(f"Processing logout request for {current_username}")
    logout_user()
    app.logger.info(f"User {current_username} logged out")
    return redirect(url_for('client_bp.home'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@fresh_login_required
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        hashed_password = flask_bcrypt.generate_password_hash(
            register_form.password.data)
        new_user = User(username=register_form.username.data, password=hashed_password,
                        secretkey=secrets.token_hex(32), apikey=secrets.token_hex(64))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth_bp.login'))
    return render_template('register.html', form=register_form, title="Register")


# @auth_bp.route("/auth/update/password", methods=["GET", "POST"])
# @fresh_login_required
# def update_password():
#     update_password_form = UpdatePasswordForm()
#     if update_password_form.validate_on_submit():
#         user = User.query.filter_by(username=current_user.username).first()
#         if user and flask_bcrypt.check_password_hash(user.password, update_password_form.oldpassword.data):
#             user.password = flask_bcrypt.generate_password_hash(update_password_form.newpassword.data)
#             db.session.commit()
#             flash("Password updated successfully")
#             return redirect(url_for('auth_bp.update_password'))
#         else:
#             flash("Incorrect password")
#             return redirect(url_for('auth_bp.update_password'))
#     return render_template('change_password.html', form=update_password_form, title="Change Password")

@auth_bp.route('/auth/clear', methods=['GET'])
@fresh_login_required
def clear():
    if not app.config['DEBUG']:
        return Response("This route is only available in DEBUG mode", status=403)
    db.drop_all()
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/auth/query', methods=['GET'])
@fresh_login_required
def query():
    return str(db.session.query(User).all())


@auth_bp.route('/auth/token', methods=['GET'])
@fresh_login_required
def token():
    return str(current_user.apikey)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@login_manager.unauthorized_handler
def unauthorized():
    return "Unauthorized to Access Requested Route", 401


@login_manager.request_loader
def load_user_from_request(request):
    app.logger.debug(f"request_loader fired for request {request}")
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != 'Bearer':
        app.logger.warning("Invalid Authorization header format")
        return None
    api_token = parts[1]
    if not api_token:
        app.logger.warning("No API key provided!")
        return None
    user = User.query.filter_by(apikey=api_token).first()
    if not user:
        app.logger.warning("No user associated with provided API key")
        return None
    app.logger.info(f"User {user.username} Loaded from API Key")
    return user
