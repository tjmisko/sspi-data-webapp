from flask import Blueprint, render_template
from wtforms import Form, StringField, SelectField, validators
from ..api.core.download import ClientDownloadForm


client_bp = Blueprint(
    'client_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/client/static'
)


@client_bp.route('/')
def home():
    return render_template('home.html')


@client_bp.route('/about')
def about():
    return render_template('about.html')


@client_bp.route('/contact')
def contact():
    return render_template('contact.html')


@client_bp.route('/data')
def data():
    download_form = ClientDownloadForm()
    return render_template('data.html', download_form=download_form)


@client_bp.route('/data/country/<CountryCode>')
def country_data(CountryCode):
    return render_template('country-template.html', CountryCode=CountryCode)


@client_bp.route('/data/indicator/<IndicatorCode>')
def indicator_data(IndicatorCode):
    return render_template('indicator-data.html', IndicatorCode=IndicatorCode)


@client_bp.route('/indicators')
def indicators():
    return render_template('indicators.html')


@client_bp.route('/methodology')
def methodology():
    return render_template('methodology.html')


@client_bp.route('/widget/<widgettype>')
def make_widget(widgettype):
    return render_template("data-widget.html", widgettype=widgettype)


@client_bp.route('/comparisons')
def comparison_home():
    return render_template("comparison-home.html")


@client_bp.route('/comparisons/sweden-france-japan')
def comparison_sweden_france_japan():
    return render_template("country-comparisons/sweden-france-japan.html")


@client_bp.route('/comparisons/china-russia-usa')
def comparison_china_russia_usa():
    return render_template("country-comparisons/china-russia-usa.html")


@client_bp.route('/comparisons/brazil-india-indonesia')
def comparison_brazil_india_indonesia():
    return render_template("country-comparisons/brazil-india-indonesia.html")


@client_bp.route('/structure')
def sspi_structure_tree():
    return render_template("sspi-structure.html")


@client_bp.route('/map')
def world_map_page():
    return render_template("world-map.html")


@client_bp.route('/globe')
def globe_tree():
    return render_template("globe.html")


@client_bp.route('/history')
def project_history():
    return render_template("history.html")


@client_bp.route('/interview')
def interview():
    return render_template("interview/tree.html")


@client_bp.route('/data/overview')
def data_overview():
    return render_template("data-overview.html")


@client_bp.route('/scores')
def overall_scores():
    return render_template("scores.html")
