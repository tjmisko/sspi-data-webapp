from flask_assets import Bundle
import sass


def scss_to_css(_in, out, **kw):
    """Custom filter to compile scss files"""
    out.write(sass.compile(string=_in.read(), output_style='compressed'))


def compile_static_assets(assets):
    """Configure bundle building and minification of css and js"""
    print("Rebuilding Static Assets")
    home_style_bundle = Bundle(
        'client_bp/sass/*.scss',
        filters=(scss_to_css, 'cssmin'),
        output='client_bp/style.css',
    )
    home_js_bundle = Bundle(
        'client_bp/dist/*.js',
        'client_bp/js/*.js',
        'client_bp/charts/*.js',
        filters='jsmin',
        output='client_bp/script.js',
    )
    assets.register('home_style_bundle', home_style_bundle)
    assets.register('home_js_bundle', home_js_bundle)
    home_js_bundle.build()
    home_style_bundle.build()
    return assets
