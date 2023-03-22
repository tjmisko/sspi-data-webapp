from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import MongoClient, PyMongo
from flask_bcrypt import Bcrypt
from flask_assets import Environment, Bundle

db = SQLAlchemy()
login_manager = LoginManager()
flask_bcrypt = Bcrypt()

client = MongoClient('localhost', 27017)
sspidb = client.flask_db
sspi_main_data = sspidb.sspi_main_data

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
        from .api import datatest, api
        # Register database
        db.create_all()
        # Register Blueprints
        app.register_blueprint(datatest.datatest_bp)
        app.register_blueprint(routes.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(api.api_bp)
        # Register Style Bundle and build optimized css, js
        assets.auto_build = True
        assets.debug = False
        home_style_bundle = Bundle(
            'home_bp/src/scss/*.scss',
            filters='pyscss,cssmin',
            output='home_bp/dist/css/style.min.css',
            extra={'rel':'stylesheet/css'}
        )
        home_js_bundle = Bundle(
            'home_bp/src/js/*.js',
            filters='jsmin',
            output='home_bp/dist/js/main.min.js'
        )
        assets.register('home_styles', home_style_bundle)
        home_style_bundle.build()
        assets.register('home_js', home_js_bundle)
        home_js_bundle.build()
        return app
