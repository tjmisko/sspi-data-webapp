from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_assets import Environment
from .assets import compile_static_assets

db = SQLAlchemy()
login_manager = LoginManager()
flask_bcrypt = Bcrypt()

client = MongoClient('localhost', 27017)
sspidb = client.flask_db
sspi_main_data_v3 = sspidb.sspi_main_data_v3
sspi_raw_api_data = sspidb.sspi_raw_api_data
sspi_clean_api_data = sspidb.sspi_clean_api_data
sspi_metadata = sspidb.sspi_metadata

assets = Environment()

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
        from .api import dashboard
        from .api.dashboard import api_bp
        from .api.core.collect import collect_bp
        from .api.core.compute import compute_bp
        # Register database
        db.create_all()
        # Register Blueprints
        app.register_blueprint(routes.home_bp)
        app.register_blueprint(auth.auth_bp)
        api_bp.register_blueprint(collect_bp)
        api_bp.register_blueprint(compute_bp)
        app.register_blueprint(dashboard.api_bp)
        
        # Register Style Bundles and build optimized css, js
        assets.init_app(app)
        if Config.FLASK_ENV == "development":
            compile_static_assets(assets)
        return app
