# load in the Flask class from the flask library
from flask import Flask, render_template, url_for
# load in the SQLAlchemy object to handle setting up the user data database
from flask_sqlalchemy import SQLAlchemy
# load in the UserMixin to handle the creation of user objects (not strictly necessary
# but it's a nice automation so we don't have to think too much about it)
from flask_login import UserMixin
# load in the packages that make the forms pretty for submitting login and
# and restration data
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

# create a Flask object
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisneedstobechanged'
db = SQLAlchemy(app)

# create a User object that can track the id, username, and password of SSPI
# team members in the database database.db
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# create a registration form for new users
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")



# create a 'route' (aka API endpoint) so that the function home is run when the
# base url is called
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/alternate')
def alternate():
    return "This is a different page!"

# run the app
# an little explanation of what's going on:
# https://www.freecodecamp.org/news/whats-in-a-python-s-name-506262fe61e8/#:~:text=The%20__name__%20variable%20(two%20underscores%20before%20and%20after,a%20module%20in%20another%20script.
if __name__ == '__main__':
    app.run(debug = True)
