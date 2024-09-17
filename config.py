from os import environ, path
from dotenv import load_dotenv
from datetime import timedelta

basedir = path.abspath(path.dirname(__file__))
print("basedir: " + basedir)
load_dotenv(path.join(basedir, '.env'))

class Config:
    # Flask config
    FLASK_ENV = 'development'
    TESTING = True
    SECRET_KEY = environ['SECRET_KEY']
    RELOAD = False
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SASS_BIN = "/env/usr/bin/pyscss"
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    REMEMBER_COOKIE_DURATION=timedelta(days=30)

class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = environ['SQLALCHEMY_DATABASE_URI']

class DevConfig(Config):
    DEBUG = True
    LOGIN_DISABLED = True
    SQLALCHEMY_DATABASE_URI = environ['SQLALCHEMY_DATABASE_URI']

class TestConfig(Config):
    DEBUG = True
    RELOAD = True
    LOGIN_DISABLED = True
    SQLALCHEMY_DATABASE_URI = environ['SQLALCHEMY_DATABASE_URI']
