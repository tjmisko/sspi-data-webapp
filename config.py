from os import environ, path
from dotenv import load_dotenv
from datetime import timedelta
import logging

basedir = path.abspath(path.dirname(__file__))
print("App Directory: " + basedir)
load_dotenv(path.join(basedir, '.env'))


class Config:
    # Flask config
    FLASK_ENV = 'development'
    LOG_LEVEL = logging.INFO
    LOG_DIR = path.join(basedir, 'logs')
    # Secure default: only DevConfig/TestConfig opt into testing/login-disabled.
    TESTING = False
    SECRET_KEY = environ['SECRET_KEY']
    RELOAD = False
    # Global backstop on request body size (256 MB). Per-endpoint input bounds
    # (utilities / customize) do the real work; this just stops absurd payloads
    # from being buffered. Admin bulk /load dumps stay well under this.
    MAX_CONTENT_LENGTH = 256 * 1024 * 1024
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    # Feature flag gating the custom-scoring per-child weight UI in the builder.
    # UI-ONLY: the scoring engine and validator always honor weights already
    # stored on a config regardless of this flag. Default OFF; override with the
    # CUSTOM_WEIGHTS_ENABLED environment variable ("1"/"true" to enable).
    CUSTOM_WEIGHTS_ENABLED = environ.get(
        "CUSTOM_WEIGHTS_ENABLED", ""
    ).strip().lower() in {"1", "true", "yes", "on"}


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    LOG_LEVEL = logging.INFO
    TESTING = False
    # Cookie hardening (F5): only send cookies over HTTPS, keep them out of JS,
    # and constrain cross-site sending. The remember-me cookie lives 30 days, so
    # protecting it in transit and against CSRF matters.
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "https"


class DevConfig(Config):
    DEBUG = True
    LOGIN_DISABLED = True
    LOG_LEVEL = logging.DEBUG


class TestConfig(Config):
    DEBUG = True
    RELOAD = False
    TESTING = True
    LOG_LEVEL = logging.DEBUG
    LOGIN_DISABLED = False
