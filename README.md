# README

## SSPI Website and Data Collection Application

This folder contains all of the code for the SSPI website and the full stack Flask application used to automatically collect and clean the dynamic data for the SSPI.  

## To run and develop the application locally:

0) If you haven't already done so, make sure you have installed a text editor (Visual Studio Code strongly recommended), git, and python3 on your system. Also ensure that a MongoDB process is running on your local machine.  The configuration assumes (in `__init__.py`) that you have you have a `MongoClient('localhost', 27017)` running on port `27017`.   Download, install, and run if necessary.
    - On MacOS, you can accomplish this via Homebrew.  Install [Homebrew](https://brew.sh/) with ```/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"``` from the command line
    - From there, run `brew update`, then `brew tap mongodb/brew`, then `brew install mongodb-community@6.0` to download and install MongoDB.
    - To start up MongoDB as a MacOS service, run `brew services start mongodb-community@6.0`
    - See the documentation [here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/) for more information, and read [here](https://www.mongodb.com/docs/manual/administration/install-community/) for a step-by-step guide for installation on other operating systems
1) Clone the application from the repo.  Navigate in your Terminal to your desired parent folder for the project and run `git clone https://github.com/tjmisko/sspi-data-collection`
2) Navigate into the new `sspi-data-collection` folder.  Create a `wsgi.py` at the top level of the directory file to boot the Flask Application.  WSGI stands for Web Server Gateway Interface and will represent the entry point for the application.  (The file is not included because the WSGI file looks different on the production configuration and contains potentially sensitive security information in addition to the code provided.) Add the following code to your new `wsgi.py` file:

```python
from sspi_flask_app import init_app
from config import DevConfig

app = init_app(DevConfig)
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
```
3) Set up a python virtual environment.  From the top level of the `sspi-data-collection`, run `python -m venv env` to create a new virtual environment.  This may take a few moments.
4) Activate your virtual environment via the activation script.  On Linux and MacOS, the command is `source env/bin/activate`.  If you're on Windows, it can vary; consult the table on [this documentation page](https://docs.python.org/3/library/venv.html) for details.
5) With your virtual environment active—this is indicated by a little ```(env)``` next to your username in the Terminal—run the command `pip install -r requirements.txt` to install all dependencies listed in the `requirements.txt` file.  This will take a little while to run.
6) Create an `instance` folder in the top level directory and insert an empty file called `database.db` your new instance folder.  The commands are `mkdir instance` and `touch database.db`. This file will serve as our user database, which is used to implement authentication.  Because many of our database routes are login protected, it will be important to implement this step to develop your application.
7) Create a `.env` file in the top level directory containing a `SECRET_KEY`, which can be any string you like (so long as its wrapped in `''`), and an `SQLALCHEMY_DATABASE_URI` which contains the absolute file path to your `database.db` file.  Remember that file paths look different on Unix vs. Windows machines.   Be sure to use the appropriate one for you.  Further, the file path must be prefixed with `sqlite:///`.  You may also have to use escape characters depending on your path—YMMV.  Here's an example of what your `.env` should look like when you're done.
```
SECRET_KEY='thiscanbewhateveryouwant'
SQLALCHEMY_DATABASE_URI='sqlite:////Users/tjmisko/Documents/sspi-data-collection/instance/database.db'
```
8) Run the `flask run` command from your terminal in the top level directory, which contains the `wsgi.py` file.  Your application should boot, and you can open it in the browser.