from flask import current_app as app
from flask_assets import Bundle


def compile_static_assets(assets):
    """Configure bundle building and minification of css and js"""
    assets.auto_build = True
    assets.debug = False
    home_style_bundle = Bundle(
        'home_bp/sass/*.scss',
        filters='pyscss,cssmin',
        output='home_bp/style.css',
    )
    home_js_bundle = Bundle(
        'home_bp/js/*.js',
        filters='jsmin',
        output='home_bp/script.js',
    )
    # # assets.config['SECRET_KEY'] = "changethis"
    # assets.config['PYSCSS_LOAD_PATHS'] = ["/Users/tristanmisko/Documents/Projects/sspi-flask-app/env/bin/pyscss"]
    # assets.config['SASS_LOAD_PATHS'] = ["bin/pyscss"]
    assets.config['PYSCSS_STATIC_URL'] = assets.url
    assets.config['PYSCSS_STATIC_ROOT'] = assets.directory
    # # assets.config['PYSCSS_ASSETS_URL'] = assets.url
    # # assets.config['PYSCSS_ASSETS_ROOT'] = assets.directory
    assets.register('home_style_bundle', home_style_bundle)
    home_style_bundle.build()
    print(home_style_bundle.resolve_contents())
    print(home_style_bundle.resolve_output())
    print(home_style_bundle.output)

    return assets