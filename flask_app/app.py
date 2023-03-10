import json
from sqlalchemy_serializer import SerializerMixin
from dataclasses import dataclass
from json import JSONEncoder
# load in the Flask class from the flask library
from flask import Flask, jsonify, render_template, request, url_for, redirect
# load in the SQLAlchemy object to handle setting up the user data database
from flask_sqlalchemy import SQLAlchemy
# load in the UserMixin to handle the creation of user objects (not strictly necessary
# but it's a nice automation so we don't have to think too much about it)
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
# load in the packages that make the forms pretty for submitting login and
# and restration data
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
# load in encryption library for passwords
from flask_bcrypt import Bcrypt
# load in pymongo for connecting to mongodb, our database
# https://www.digitalocean.com/community/tutorials/how-to-use-mongodb-in-a-flask-application
from pymongo import MongoClient
from bson import json_util
import requests

# create a Flask object
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/tristanmisko/Documents/Projects/sspi-data-collection/flask_app/instance/database.db'
app.config['SECRET_KEY'] = 'thisneedstobechanged'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# MongoDB Configuration
client = MongoClient('localhost', 27017)
sspidb = client.flask_db
sspi_main_data = sspidb.sspi_main_data

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# create a User object that can track the id, username, and password of SSPI
# team members in the database database.db
@dataclass
class User(db.Model, UserMixin, SerializerMixin):
    id:int = db.Column(db.Integer, primary_key=True)
    username:str = db.Column(db.String(20), nullable=False, unique=True)
    password:str = db.Column(db.String(80), nullable=False)


# create a registration form for new users
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        # query the database to check whether the submitted new username is taken
        username_taken = User.query.filter_by(username=username.data).first()
        # if the username is taken, raise a validation ValidationError
        if username_taken:
            raise ValidationError("That username is already taken!")

# create a registration form for new users
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

# create a 'route' (aka API endpoint) so that the function home is run when the
# base url is called
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/database', methods=['GET', 'POST'])
def database():
    if request.method == 'POST':
        indicator = request.form['indicator']
        country = request.form['country']
        value = request.form['value']
        year = request.form['year'] 
        sspi_main_data.insert_one({"indicator": indicator,
                                   "value": value,
                                   "country": country,
                                   "year": year})
        return redirect(url_for('database'))
    else:
        sspi_data = sspi_main_data.find()
        for doc in sspi_data:
            print(doc)
    return "database page"

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))               
    return render_template('login.html', form=login_form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(register_form.password.data)
        new_user = User(username=register_form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=register_form)

@app.route('/collect-iea-data')
def collect_coal_power():
    response = requests.get("https://api.iea.org/stats/indicator/TESbySource?countries=BEL").json()
    for r in response:
        print(r, type(r))
        sspi_main_data.insert_one(r)
    return str(len(response))

@app.route('/check_db')
def check_db():
    x = sspi_main_data.find()
    print(x)
    return "1"

@app.route('/check-user-db')
@login_required
def get_all_users():
    users = User.query.all()
    return str(users)

# run the app
# an little explanation of what's going on:
# https://www.freecodecamp.org/news/whats-in-a-python-s-name-506262fe61e8/#:~:text=The%20__name__%20variable%20(two%20underscores%20before%20and%20after,a%20module%20in%20another%20script.
if __name__ == '__main__':
    app.run(debug = True)

def parse_json(data):
    return json.loads(json_util.dumps(data))