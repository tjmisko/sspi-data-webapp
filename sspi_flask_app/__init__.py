from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# from werkzeug.middleware.profiler import ProfilerMiddleware
from flask_bcrypt import Bcrypt
from flask_assets import Environment
from sspi_flask_app.assets import compile_static_assets
from sspi_flask_app.logging import configure_logging
from sspi_flask_app.models.usermodel import db
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_main_data_v3
)
from sspi_flask_app.api.core.compute.SUS import (
    compute_eco,
    compute_lnd,
    compute_ghg,
    compute_nrg,
    compute_wst
)

from sspi_flask_app.api.core.compute.MS import (
    compute_wen,
    compute_wwb,
    compute_tax,
    compute_fin,
    compute_neq
)
from sspi_flask_app.api.core.compute.PG import (
    compute_edu,
    compute_hlc,
    compute_inf,
    compute_rts,
    compute_saf,
    compute_glb
)
from sspi_flask_app.api.core.compute.Outcome import (
    compute_gdp
)

login_manager = LoginManager()
flask_bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200000 per day", "50000 per hour"],
    storage_uri='mongodb://localhost:27017',
    strategy="fixed-window"
)
assets = Environment()


def init_app(Config):
    # Initialize Core application
    app = Flask(__name__)
    app.config.from_object(Config)
    # app.wsgi_app = ProfilerMiddleware(
    #     app.wsgi_app,
    #     restrictions=[5],
    #     profile_dir="profiler"
    # )
    db.init_app(app)
    flask_bcrypt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    assets.init_app(app)

    with app.app_context():
        if Config.RELOAD or sspi_main_data_v3.is_empty():
            sspi_main_data_v3.load()
        if Config.RELOAD or sspi_metadata.is_empty():
            sspi_metadata.load()
        # Import All Blueprints
        from sspi_flask_app.client.routes import client_bp
        from sspi_flask_app.auth.routes import auth_bp
        from sspi_flask_app.api.api import api_bp
        from sspi_flask_app.api.core.collect import collect_bp
        from sspi_flask_app.api.core.compute import compute_bp
        from sspi_flask_app.api.core.dashboard import dashboard_bp
        from sspi_flask_app.api.core.delete import delete_bp
        from sspi_flask_app.api.core.finalize import finalize_bp
        from sspi_flask_app.api.core.host import host_bp
        from sspi_flask_app.api.core.impute import impute_bp
        from sspi_flask_app.api.core.load import load_bp
        from sspi_flask_app.api.core.sync import sync_bp
        from sspi_flask_app.api.core.query import query_bp
        from sspi_flask_app.api.core.save import save_bp
        # Register database
        db.create_all()
        # Register Blueprints
        api_bp.register_blueprint(collect_bp)
        api_bp.register_blueprint(compute_bp)
        api_bp.register_blueprint(dashboard_bp)
        api_bp.register_blueprint(delete_bp)
        api_bp.register_blueprint(finalize_bp)
        api_bp.register_blueprint(host_bp)
        api_bp.register_blueprint(impute_bp)
        api_bp.register_blueprint(load_bp)
        api_bp.register_blueprint(sync_bp)
        api_bp.register_blueprint(query_bp)
        api_bp.register_blueprint(save_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(client_bp)
        app.register_blueprint(auth_bp)

        configure_logging(app)
        if Config.FLASK_ENV == "development":
            assets.auto_build = True
            assets.debug = True
            compile_static_assets(assets)
        app.logger.info("Application Initialized")
        return app
