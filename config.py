from os import environ, path
from dotenv import load_dotenv
from datetime import timedelta
import logging

basedir = path.abspath(path.dirname(__file__))
print("App Directory: " + basedir)
load_dotenv(path.join(basedir, '.env'))


class Config:
    # Flask config
    FLASK_ENV = 'development'
    LOG_LEVEL = logging.INFO
    LOG_DIR = path.join(basedir, 'logs')
    TESTING = True
    SECRET_KEY = environ['SECRET_KEY']
    RELOAD = False
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    LOG_LEVEL = logging.DEBUG
    TESTING = False


class DevConfig(Config):
    DEBUG = True
    LOGIN_DISABLED = True
    LOG_LEVEL = logging.DEBUG


class TestConfig(Config):
    DEBUG = True
    RELOAD = False
    TESTING = True
    LOG_LEVEL = logging.DEBUG
    LOGIN_DISABLED = False
