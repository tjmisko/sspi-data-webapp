from flask import Flask
from flask_app.config import Config, DevConfig, ProdConfig
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient, PyMongo

db = SQLAlchemy()

client = MongoClient('localhost', 27017)
sspidb = client.flask_db
sspi_main_data = sspidb.sspi_main_data

def init_app():
    # Initialize Core application
    app = Flask(__name__)
    app.config.from_object(DevConfig)
    print("DatabaseURI:" + DevConfig.SQLALCHEMY_DATABASE_URI)
    # Initialize Plugins
    db.init_app(app)
    
    with app.app_context():
        return app
