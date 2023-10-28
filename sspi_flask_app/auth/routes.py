from functools import wraps
import secrets
import string
from flask import current_app as app, jsonify
import pyotp
from ..models.usermodel import User, db
from .. import login_manager, flask_bcrypt
from sqlalchemy_serializer import SerializerMixin
# load in the Flask class from the flask library
from flask import Flask, render_template, request, url_for, redirect, Blueprint, flash
# load in the SQLAlchemy object to handle setting up the user data database
from flask_sqlalchemy import SQLAlchemy
# load in the UserMixin to handle the creation of user objects (not strictly necessary
# but it's a nice automation so we don't have to think too much about it)
from flask_login import fresh_login_required, login_user, LoginManager, login_required, logout_user, current_user
# load in the packages that make the forms pretty for submitting login and
# and restration data
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, ValidationError, Regexp
# load in encryption library for passwords
from dataclasses import dataclass
import time
from urllib.parse import urljoin, urlparse

auth_bp = Blueprint(
    'auth_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

login_manager.login_view = "auth_bp.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

# create a registration form for new users
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
                message="Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character."
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

# create a login form
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"}, label="Username")
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"}, label="Password")
    remember_me = BooleanField(default=False, label="Remember me for 30 days")
    submit = SubmitField("Login as Administrator")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print(request.args.get("next"))
    if current_user.is_authenticated:
        return redirect(url_for('client_bp.data'))
    if 'Authorization' in request.headers:
        api_key = request.headers['Authorization']
        user = User.query.filter_by(api_key=api_key).first()
        login_user(user)
    login_form = LoginForm()
    if not login_form.validate_on_submit():
        flash("Invalid Submission Format")
        return render_template('login.html', form=login_form, error="Invalid Submission Format")
    user = User.query.filter_by(username=login_form.username.data).first()
    if user is None or not flask_bcrypt.check_password_hash(user.password, login_form.password.data):
        flash("Invalid username or password")
        return render_template('login.html', form=login_form, error="Invalid username or password")
    if login_form.remember_me:
        login_user(user, remember=True, duration=app.config['REMEMBER_COOKIE_DURATION'])
    login_user(user)
    flash("Login Successful! Redirecting...")
    return redirect(url_for('api_bp.api_home'))               

@auth_bp.route('/remote/session/login', methods=['POST'])
def remote_login():
    print(request.__attrs__)
    username = request.text.get("username")
    print(request)
    print(f"{username}\n")
    # password = request.data.get("password")
    # print(f"{password}\n")
    password = "wrong"
    user = User.query.filter_by(username=username).first()
    if user and flask_bcrypt.check_password_hash(user.password, password):
        login_user(user)
        print(current_user.username)
    return redirect(url_for('api_bp.api_home'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('client_bp.home'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@fresh_login_required
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        hashed_password = flask_bcrypt.generate_password_hash(register_form.password.data)
        new_user = User(username=register_form.username.data, password=hashed_password, secretkey=pyotp.random_base32(), apikey=secrets.token_hex(64))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth_bp.login'))
    return render_template('register.html', form=register_form)

@auth_bp.route("/auth/update/password", methods=["GET", "POST"])
@fresh_login_required
def update_password():
    update_password_form = UpdatePasswordForm()
    if update_password_form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        if user and flask_bcrypt.check_password_hash(user.password, update_password_form.oldpassword.data):
            user.password = flask_bcrypt.generate_password_hash(update_password_form.newpassword.data)
            db.session.commit()
            flash("Password updated successfully")
            return redirect(url_for('auth_bp.update_password'))
        else:
            flash("Incorrect password")
            return redirect(url_for('auth_bp.update_password'))
    return render_template('update_password.html', form=update_password_form)

@auth_bp.route('/auth/clear', methods=['GET'])
@fresh_login_required
def clear():
    db.session.query(User).delete()
    db.session.commit()
    return redirect(url_for('auth_bp.query'))

@auth_bp.route('/auth/query', methods=['GET'])
@login_required
def query():
    return str(db.session.query(User).all())

def is_safe_url(target):
    """
    This could be made very safe by checking the target against a list of safe urls on my site
    """ 
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# def login_required(func):
#     @wraps(func)
#     def decorated_view(*args, **kwargs):
#         if not current_user.is_authenticated:
#             return app.login_manager.unauthorized()

#         # flask 1.x compatibility
#         # current_app.ensure_sync is only available in Flask >= 2.0
#         if callable(getattr(app, "ensure_sync", None)):
#             return current_app.ensure_sync(func)(*args, **kwargs)
#         return func(*args, **kwargs)
#     return decorated_view