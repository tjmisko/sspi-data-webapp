from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
print("basedir: " + basedir)
load_dotenv(path.join(basedir, '.env'))

class Config:
    # Flask config
    FLASK_ENV = 'development'
    TESTING = True
    SECRET_KEY = environ.get('SECRET_KEY')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SASS_BIN = "/env/usr/bin/pyscss"
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True
    REMEMBER_COOKIE_DURATION=60*60*24*30

class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')

class DevConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
