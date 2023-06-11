# README

## SSPI Website and Data Collection Application

This folder contains all of the code for the SSPI website and the full stack Flask application used to automatically collect and clean the dynamic data for the SSPI.  

## To run and develop the application locally:

1) Create a `wsgi.py` file to boot the application.  WSGI stands for Web Server Gateway Interface and will represent the entry point for the application.  Thge file is not included because the WSGI file looks different on the production configuration and contains potentially sensitive security information in addition to the code provided. Add the following code to the new `wsgi.py` file:

```
from sspi_flask_app import init_app
from config import DevConfig

app = init_app(DevConfig)
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
```

2) Create an `instance` folder in the top level directory and insert an empty file called `database.db`.  This will be our authorization database

3) Create a `.env` file in the top level directory containing a `SECRET_KEY`, which can be anything you like, and an `SQLALCHEMY_DATABASE_URI` which contains the filepath to your 

3) Set up a virtual python environment in the `env` folder provided.  Activate your virtual environment and install all packages from the `requirements.txt` file included.  

4) Make sure you are running a MongoDB client on your local machine.  Download and install if necessary.

5) Run the `flask run` command from your terminal in the top level directory containing the `wsgi.py` file.

