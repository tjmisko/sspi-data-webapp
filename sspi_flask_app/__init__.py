from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# from werkzeug.middleware.profiler import ProfilerMiddleware
from flask_bcrypt import Bcrypt
from flask_assets import Environment
from sspi_flask_app.assets import compile_static_assets
from sspi_flask_app.logging import configure_logging
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_static_metadata,
    sspi_static_data_2018,
    sspi_user_data
)

import sspi_flask_app.api.core.sspi.sus.eco.biodiv
import sspi_flask_app.api.core.sspi.sus.eco.redlst
import sspi_flask_app.api.core.sspi.sus.ghg.beefmk
import sspi_flask_app.api.core.sspi.sus.ghg.coalpw
import sspi_flask_app.api.core.sspi.sus.ghg.gtrans
import sspi_flask_app.api.core.sspi.sus.lnd.carbon
import sspi_flask_app.api.core.sspi.sus.lnd.chmpol
import sspi_flask_app.api.core.sspi.sus.lnd.defrst
import sspi_flask_app.api.core.sspi.sus.lnd.nitrog
import sspi_flask_app.api.core.sspi.sus.lnd.watman
import sspi_flask_app.api.core.sspi.sus.nrg.airpol
import sspi_flask_app.api.core.sspi.sus.nrg.altnrg
import sspi_flask_app.api.core.sspi.sus.nrg.nrgint
import sspi_flask_app.api.core.sspi.sus.wst.mswgen
import sspi_flask_app.api.core.sspi.sus.wst.recycl
import sspi_flask_app.api.core.sspi.sus.wst.stcons
import sspi_flask_app.api.core.sspi.ms.fin.fdepth
import sspi_flask_app.api.core.sspi.ms.fin.fstabl
import sspi_flask_app.api.core.sspi.ms.fin.pubacc
import sspi_flask_app.api.core.sspi.ms.neq.ginipt
import sspi_flask_app.api.core.sspi.ms.neq.ishrat
import sspi_flask_app.api.core.sspi.ms.tax.crptax
import sspi_flask_app.api.core.sspi.ms.tax.txrdst
import sspi_flask_app.api.core.sspi.ms.tax.taxrev
import sspi_flask_app.api.core.sspi.ms.wen.colbar
import sspi_flask_app.api.core.sspi.ms.wen.employ
import sspi_flask_app.api.core.sspi.ms.wwb.fatinj
import sspi_flask_app.api.core.sspi.ms.wwb.matern
import sspi_flask_app.api.core.sspi.ms.wwb.senior
import sspi_flask_app.api.core.sspi.ms.wwb.unempb
import sspi_flask_app.api.core.sspi.pg.edu.enrpri
import sspi_flask_app.api.core.sspi.pg.edu.enrsec
import sspi_flask_app.api.core.sspi.pg.edu.puptch
import sspi_flask_app.api.core.sspi.pg.edu.yrsedu
import sspi_flask_app.api.core.sspi.pg.glb.armexp
import sspi_flask_app.api.core.sspi.pg.glb.foraid
import sspi_flask_app.api.core.sspi.pg.glb.milexp
import sspi_flask_app.api.core.sspi.pg.glb.rdfund
import sspi_flask_app.api.core.sspi.pg.hlc.atbrth
import sspi_flask_app.api.core.sspi.pg.hlc.cstunt
import sspi_flask_app.api.core.sspi.pg.hlc.dptcov
import sspi_flask_app.api.core.sspi.pg.hlc.fampln
import sspi_flask_app.api.core.sspi.pg.hlc.physpc
import sspi_flask_app.api.core.sspi.pg.inf.aqelec
import sspi_flask_app.api.core.sspi.pg.inf.drkwat
import sspi_flask_app.api.core.sspi.pg.inf.intrnt
import sspi_flask_app.api.core.sspi.pg.inf.sansrv
import sspi_flask_app.api.core.sspi.pg.inf.trnetw
import sspi_flask_app.api.core.sspi.pg.rts.edemoc
import sspi_flask_app.api.core.sspi.pg.rts.gendeq
import sspi_flask_app.api.core.sspi.pg.rts.pubsrv
import sspi_flask_app.api.core.sspi.pg.rts.rulelw
import sspi_flask_app.api.core.sspi.pg.rts.unconv
import sspi_flask_app.api.core.sspi.pg.saf.cybsec
import sspi_flask_app.api.core.sspi.pg.saf.murder
import sspi_flask_app.api.core.sspi.pg.saf.prison
import sspi_flask_app.api.core.sspi.pg.saf.secapp


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
    flask_bcrypt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    assets.init_app(app)

    with app.app_context():
        if Config.RELOAD or sspi_static_data_2018.is_empty():
            sspi_static_data_2018.load()
        if Config.RELOAD or sspi_static_metadata.is_empty():
            sspi_static_metadata.load()
        if Config.RELOAD or sspi_metadata.is_empty():
            sspi_metadata.load()
        # Import All Blueprints
        from sspi_flask_app.client.routes import client_bp
        from sspi_flask_app.auth.routes import auth_bp
        from sspi_flask_app.api.api import api_bp
        from sspi_flask_app.api.core.sspi import compute_bp
        from sspi_flask_app.api.core.sspi import impute_bp
        from sspi_flask_app.api.core.dataset import dataset_bp
        from sspi_flask_app.api.core.dashboard import dashboard_bp
        from sspi_flask_app.api.core.delete import delete_bp
        from sspi_flask_app.api.core.download import download_bp
        from sspi_flask_app.api.core.finalize import finalize_bp
        from sspi_flask_app.api.core.host import host_bp
        from sspi_flask_app.api.core.load import load_bp
        from sspi_flask_app.api.core.query import query_bp
        from sspi_flask_app.api.core.save import save_bp
        from sspi_flask_app.api.core.customize import customize_bp
        # Initialize MongoDB indexes for user data
        sspi_user_data.create_indexes()
        # Initialize MongoDB indexes for custom structure data
        from sspi_flask_app.models.database import sspi_custom_user_structure
        sspi_custom_user_structure.create_indexes()
        # Register Blueprints
        api_bp.register_blueprint(dataset_bp)
        api_bp.register_blueprint(compute_bp)
        api_bp.register_blueprint(dashboard_bp)
        api_bp.register_blueprint(delete_bp)
        api_bp.register_blueprint(download_bp)
        api_bp.register_blueprint(finalize_bp)
        api_bp.register_blueprint(host_bp)
        api_bp.register_blueprint(impute_bp)
        api_bp.register_blueprint(load_bp)
        api_bp.register_blueprint(query_bp)
        api_bp.register_blueprint(save_bp)
        api_bp.register_blueprint(customize_bp)
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
