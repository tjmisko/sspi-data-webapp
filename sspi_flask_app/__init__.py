from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient, PyMongo
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
flask_bcrypt = Bcrypt()

client = MongoClient('localhost', 27017)
sspidb = client.flask_db
sspi_main_data = sspidb.sspi_main_data

def init_app(Config):
    # Initialize Core application
    app = Flask(__name__)
    app.config.from_object(Config)
    print("DatabaseURI:" + Config.SQLALCHEMY_DATABASE_URI)
    # Initialize SQLAlchemy Database
    db.init_app(app)
    # Initialize password encryption
    flask_bcrypt.init_app(app)
    # Initialize Login manager
    login_manager.init_app(app)

    with app.app_context():
        # read in the appropriate modules
        from .home import routes
        from .auth import auth
        from .api import datatest, api
        # Register database
        db.create_all()
        # Register Blueprints
        app.register_blueprint(datatest.datatest_bp)
        app.register_blueprint(routes.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(api.api_bp)
        return app
