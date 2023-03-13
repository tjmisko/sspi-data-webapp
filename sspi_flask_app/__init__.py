from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient, PyMongo
from config import Config, DevConfig, ProdConfig

db = SQLAlchemy()

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

    login_manager = LoginManager()
    login_manager.init_app(app)
    
    with app.app_context():
        from .home import routes
        from .auth import auth
        # Register Blueprints
        db.create_all()
        app.register_blueprint(routes.home_bp)
        app.register_blueprint(auth.auth_bp)
        return app
