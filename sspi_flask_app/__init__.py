from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_assets import Environment
from sspi_flask_app.models.database import MongoWrapper, SSPIRawAPIData, SSPIMetadata
from .assets import compile_static_assets

db = SQLAlchemy()
login_manager = LoginManager()
flask_bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

client = MongoClient('localhost', 27017)
sspidb = client.flask_db

sspi_main_data_v3 = MongoWrapper(sspidb.sspi_main_data_v3)
sspi_metadata = SSPIMetadata(sspidb.sspi_metadata)


sspi_raw_api_data = SSPIRawAPIData(sspidb.sspi_raw_api_data)
sspi_bulk_data = MongoWrapper(sspidb.sspi_bulk_data)
sspi_clean_api_data = MongoWrapper(sspidb.sspi_clean_api_data)
sspi_imputed_data = MongoWrapper(sspidb.sspi_imputed_data)
sspi_analysis = MongoWrapper(sspidb.sspi_analysis)
sspi_dynamic_data = MongoWrapper(sspidb.sspi_dynamic_data)

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
    # Initialize API rate limiter
    limiter.init_app(app)

    with app.app_context():
        # read in the appropriate modules
        # sspi_main_data_v3.load()
        sspi_metadata.load()
        from .client.routes import client_bp
        from .auth.routes import auth_bp
        from .api.api import api_bp
        from .api.core.collect import collect_bp
        from .api.core.compute import compute_bp
        from .api.core.dashboard import dashboard_bp
        from .api.core.delete import delete_bp
        from .api.core.download import download_bp
        from .api.core.impute import impute_bp
        from .api.core.load import load_bp
        from .api.core.query import query_bp
        from .api.core.save import save_bp
        from .api.core.test import test_bp

        # Register database
        db.create_all()
        # Register Blueprints
        app.register_blueprint(client_bp)
        app.register_blueprint(auth_bp)
        api_bp.register_blueprint(collect_bp)
        api_bp.register_blueprint(compute_bp)
        api_bp.register_blueprint(dashboard_bp)
        api_bp.register_blueprint(delete_bp)
        api_bp.register_blueprint(download_bp)
        api_bp.register_blueprint(impute_bp)
        api_bp.register_blueprint(load_bp)
        api_bp.register_blueprint(query_bp)
        api_bp.register_blueprint(save_bp)
        api_bp.register_blueprint(test_bp)
        app.register_blueprint(api_bp)
        
        # Register Style Bundles and build optimized css, js
        if Config.FLASK_ENV == "development":
            compile_static_assets(assets)
        assets.init_app(app)
        return app
