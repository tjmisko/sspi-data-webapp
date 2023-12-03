from flask import current_app as app
from flask_assets import Bundle
import sass

def custom_scss_filter(_in, out, **kw):
    """Custom filter to compile scss files"""
    sass.compile(filename=scss_file, output_style='compressed', include_paths=['client_bp/sass/'])
    with open(out, 'r') as f:
        return f.read()

def compile_static_assets(assets):
    """Configure bundle building and minification of css and js"""
    assets.auto_build = False
    assets.debug = False
    home_style_bundle = Bundle(
        'client_bp/sass/*.scss',
        filters=(custom_scss_filter, 'cssmin'),
        output='client_bp/style.css',
    )
    home_js_bundle = Bundle(
        'client_bp/js/*.js',
        filters='jsmin',
        output='client_bp/script.js',
    )
    # # assets.config['SECRET_KEY'] = "changethis"
    # assets.config['PYSCSS_LOAD_PATHS'] = ["/Users/tristanmisko/Documents/Projects/sspi-flask-app/env/bin/pyscss"]
    # assets.config['SASS_LOAD_PATHS'] = ["bin/pyscss"]
    assets.config['PYSCSS_STATIC_URL'] = assets.url
    assets.config['PYSCSS_STATIC_ROOT'] = assets.directory
    # # assets.config['PYSCSS_ASSETS_URL'] = assets.url
    # # assets.config['PYSCSS_ASSETS_ROOT'] = assets.directory
    assets.register('home_style_bundle', home_style_bundle)
    assets.register('home_js_bundle', home_js_bundle)
    home_js_bundle.build()
    home_style_bundle.build()
    return assets
