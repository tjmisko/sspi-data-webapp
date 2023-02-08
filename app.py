# load in the Flask class from the flask library
from flask import Flask, render_template

# create a Flask object
app = Flask(__name__)

# create a 'route' so that the function home is run when the
# base url is called
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/alternate')
def alternate():
    return "This is a different page!"

# run the app
# an little explanation of what's going on:
# https://www.freecodecamp.org/news/whats-in-a-python-s-name-506262fe61e8/#:~:text=The%20__name__%20variable%20(two%20underscores%20before%20and%20after,a%20module%20in%20another%20script.
if __name__ == '__main__':
    app.run()
