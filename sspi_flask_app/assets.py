from flask_assets import Bundle

def compile_static_assets(assets):
    """Configure bundle building and minification of css and js"""
    print("Rebuilding Static Assets")
    home_style_bundle = Bundle(
        'client_bp/css/variables.css',
        'client_bp/css/base.css',
        'client_bp/css/components/*.css',
        'client_bp/css/templates/*.css',
        'client_bp/css/charts/*.css',
        'client_bp/css/pages/*.css',
        filters='cssmin',
        output='client_bp/style.css',
    )
    home_js_bundle = Bundle(
        'client_bp/dist/*.js',
        'client_bp/js/*.js',
        'client_bp/js/components/*.js',
        'client_bp/charts/plugins/extrapolate-backward-plugin.js',
        'client_bp/charts/plugins/chart-interaction-plugin.js',
        'client_bp/charts/plugins/pillar-breakdown-interaction-plugin.js',
        'client_bp/charts/plugins/series-correlation-tooltip.js',
        'client_bp/charts/plugins/shift-rotated-ticks-plugin.js',
        'client_bp/charts/components/*.js',
        'client_bp/charts/panel/panel-chart.js',
        'client_bp/charts/panel/series-panel-chart.js',
        'client_bp/charts/panel/dataset-panel-chart.js',
        'client_bp/charts/panel/score-panel-chart.js',
        'client_bp/charts/panel/indicator-panel-chart.js',
        'client_bp/charts/panel/sspi-panel-chart.js',
        'client_bp/charts/panel/country-pillar-panel-chart.js',
        'client_bp/charts/static/*.js',
        'client_bp/charts/dynamic/*.js',
        'client_bp/charts/matrix/*.js',
        filters='jsmin',
        output='client_bp/script.js',
    )
    assets.register('home_style_bundle', home_style_bundle)
    assets.register('home_js_bundle', home_js_bundle)
    home_js_bundle.build()
    home_style_bundle.build()
    return assets
