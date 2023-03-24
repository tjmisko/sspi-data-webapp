from flask import current_app as app
from flask_assets import Bundle

def compile_static_assets(assets):
    """Configure bundle building and minification of css and js"""
    assets.auto_build = True
    assets.debug = False
    home_style_bundle = Bundle(
        'home_bp/sass/*.scss',
        filters='scss,cssmin',
        output='home_bp/style.css',
    )
    # assets.config['SECRET_KEY'] = "changethis"
    # assets.config['PYSCSS_LOAD_PATHS'] = assets.url
    # assets.config['PYSCSS_STATIC_URL'] = assets.url
    # assets.config['PYSCSS_STATIC_ROOT'] = assets.directory
    # assets.config['PYSCSS_ASSETS_URL'] = assets.url
    # assets.config['PYSCSS_ASSETS_ROOT'] = assets.directory
    assets.register('home_style_bundle', home_style_bundle)
    home_style_bundle.build()
    return assets