## SSPI Website and Data Processing Application

This repository contains the code for the SSPI website, including that used to collect and clean the time-series data for the SSPI from sources on the web.

## To run and develop the application locally:

0) If you haven't already done so, make sure you have installed a text editor (Visual Studio Code is a fine starting point), `git`, and `python` (version 3.12.9 works; other versions may as wellpython3) on your system. Also ensure that a MongoDB process is running on your local machine.  The configuration assumes (in `__init__.py`) that you have you have a `MongoClient('localhost', 27017)` running on port `27017`.   Download, install, and run if necessary.
    - On MacOS, you can accomplish this via Homebrew.  Install [Homebrew](https://brew.sh/) with ```/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"``` from the command line. 
    - From there, run `brew update`, then `brew tap mongodb/brew`, then `brew install mongodb-community@6.0` to download and install MongoDB.
    - To start up MongoDB as a MacOS service, run `brew services start mongodb-community@6.0`
    - See the documentation [here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/) for more information, and read [here](https://www.mongodb.com/docs/manual/administration/install-community/) for a step-by-step guide for installation on other operating systems.
    - On Windows, I highly recommend setting up a Unix-like environment to be able to use the commands in this README. Installing Git Bash or Windows Subsystem for Linux (WSL) is recommended.
1) Clone the application from the repo.  Navigate in your terminal to your desired system directory for the project and run `git clone https://github.com/tjmisko/sspi-data-webapp`. This will create a new repository directory called `sspi-data-webapp` containing most of what you need to run the application. You will provide the remaining necessary components in the following steps.
2) Navigate into the new `sspi-data-webapp` folder.  Create a file called `wsgi.py` at the top level of the repository. This will be used to boot the Flask Application.  WSGI stands for Web Server Gateway Interface and will represent the entry point for the application.  (The file is not included because the WSGI file looks different on the production configuration and contains potentially sensitive security information in addition to the code provided.) Add the following code to your new `wsgi.py` file:

```python
from sspi_flask_app import init_app
from config import DevConfig

app = init_app(DevConfig)
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
```
3) Set up a python virtual environment.  From the top level of the `sspi-data-webapp` run `python -m venv env` to create a new virtual environment.  This may take a few moments.
    > Setting up a python virtual environment is crucial for the application because it ensures that the correct versions of the necessary packages are installed and will be executed when the environment is active. All it means "activate your virtual environment" is to place a particular set of directories (those in the `env` folder created in this step) at the front of your `PATH`. This means that your computer will find the correct versions, stored here, before it goes off to look for other versions that may be found elsewhere on your system.
4) Activate your virtual environment via the activation script.  On Linux and MacOS, the command is `source env/bin/activate`.  If you're on Windows, the correct command may be different; consult the table on [this documentation page](https://docs.python.org/3/library/venv.html) for details.
5) With your virtual environment active—this is indicated by a little ```(env)``` next to your username in the Terminal—run the command `pip install -r requirements.txt` to install all dependencies listed in the `requirements.txt` file.  This will take a little while to run.
6) Create an `instance` folder in the top level directory and insert an empty file called `database.db` your new instance folder.  The commands are `mkdir instance` and `touch database.db`. This file will serve as our user database, which is used to implement authentication.  Because many of our database routes are login protected, it will be important to implement this step to develop your application.
7) Create a `.env` file in the top level directory containing a `SECRET_KEY`, which can be any string you like for development so long as its wrapped in `''`), and an `SQLALCHEMY_DATABASE_URI` which contains the absolute file path to your `database.db` file.  Remember that file paths look different on Unix vs. Windows machines.   Be sure to use the appropriate one for you.  Further, the file path must be prefixed with `sqlite:///`.  You may also have to use escape characters depending on your path—YMMV.  Here's an example of what your `.env` should look like when you're done.
```
SECRET_KEY='thiscanbewhateveryouwant'
SQLALCHEMY_DATABASE_URI='sqlite:////home/tjmisko/Projects/sspi-data-webapp/instance/database.db'
```

8) Run the `flask run` command from your terminal in the top level directory, which contains the `wsgi.py` file.  Your application should boot, and you can open it in the browser.
    > Use `flask run --debug` to run the application in debug mode. This will cause the application to automatically reload when making changes, saving you a whole lot of `Ctrl-C` and up-arrows.
9) In order to run `@login_protected` routes, you will need to register yourself in the SSPI database. To do this, navigate to the `/register` route in your browser and fill out the form.  You will be redirected to the login page, where you can enter your credentials and access the protected routes. Otherwise, you will receive an error message upon running `/api/v1/collect` routes which will prevent you from collecting data.
