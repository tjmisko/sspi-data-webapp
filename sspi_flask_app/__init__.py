from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient, PyMongo
from config import Config, DevConfig, ProdConfig
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()

client = MongoClient('localhost', 27017)
sspidb = client.flask_db
sspi_main_data = sspidb.sspi_main_data

def init_app():
    # Initialize Core application
    app = Flask(__name__)
    app.config.from_object(DevConfig)
    print("DatabaseURI:" + DevConfig.SQLALCHEMY_DATABASE_URI)
    # Initialize SQLAlchemy Database
    db.init_app(app)
    # Initialize Login manager
    login_manager.init_app(app)
    # initialize Bcrypt
    bcrypt = Bcrypt(app)

    with app.app_context():
        from .home import routes
        from .auth import auth
        from .models import usermodel
        # Register Blueprints
        db.create_all()
        app.register_blueprint(routes.home_bp)
        app.register_blueprint(auth.auth_bp)
        return app
