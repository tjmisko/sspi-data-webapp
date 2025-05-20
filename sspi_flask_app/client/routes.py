from flask import Blueprint, render_template, request, url_for, current_app as app
from flask_login import login_required
import re
import pycountry
from sspi_flask_app.api.resources.utilities import parse_json


client_bp = Blueprint(
    'client_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/client/static'
)


@client_bp.route('/')
def home():
    return render_template('home.html')


@client_bp.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@client_bp.route('/about')
def about():
    return render_template('about.html')


@client_bp.route('/contact')
def contact():
    return render_template('contact.html')


@client_bp.route('/data')
def data():
    return render_template('data.html')


@client_bp.route('/data/country/<CountryCode>')
def country_data(CountryCode):
    return render_template('country-template.html', CountryCode=CountryCode)


@client_bp.route('/data/indicator/<IndicatorCode>')
def indicator_data(IndicatorCode):
    return render_template('indicator-data.html', IndicatorCode=IndicatorCode)


@client_bp.route('/data/category/<CategoryCode>')
def category_data(CategoryCode):
    return render_template('category-data.html', CategoryCode=CategoryCode)


@client_bp.route('/indicators')
def indicators():
    return render_template('indicators.html')


@client_bp.route('/methodology')
def methodology():
    return render_template('methodology.html')


@client_bp.route('/widget/<widgettype>')
def make_widget(widgettype):
    return render_template("data-widget.html", widgettype=widgettype)


@client_bp.route('/compare')
def compare_home():
    return render_template("compare-home.html")


@client_bp.route('/compare/custom', methods=['POST'])
def compare_custom():
    def bind_country_information(selection, index):
        if len(selection) == 0 and index < 2:
            raise LookupError("Please provide a country name.")
        if len(selection) == 0 and index == 2:
            return None, None
        selection_match = re.match(r'([A-Za-z ]+)\(([A-Z]{3})\)$', selection)
        if selection_match:
            country_code = selection_match.group(2)
            country_name = selection_match.group(1)
            country_name = pycountry.countries.get(alpha_3=country_code).name
        else:
            try:
                country_guess = pycountry.countries.search_fuzzy(selection)
            except LookupError:
                raise LookupError(
                    f"Country not found for query '{selection}'.")
            country_guess = pycountry.countries.search_fuzzy(selection)
            country_code = country_guess[0].alpha_3
            country_name = country_guess[0].name
        return country_code, country_name
    country_data = request.get_json()
    if not len(country_data.keys()) == 3:
        return "Please select exactly three countries to compare."
    country_codes = []
    country_names = []
    for i, country_string in enumerate(country_data.values()):
        try:
            code, name = bind_country_information(country_string, i)
        except LookupError as e:
            return str(e)
        if code is not None:
            country_codes.append(code)
        if name is not None:
            country_names.append(name)
    comparison_list = [{'code': code, 'name': name}
                       for code, name in zip(country_codes, country_names)]
    print(comparison_list)
    return parse_json({
        "html": render_template("compare/comparison-result.html", comparison_list=comparison_list),
        "data": comparison_list
    })


@client_bp.route('/compare/sweden-france-japan')
def compare_sweden_france_japan():
    return render_template("compare/sweden-france-japan.html")


@client_bp.route('/compare/china-russia-usa')
def compare_china_russia_usa():
    return render_template("compare/china-russia-usa.html")


@client_bp.route('/compare/brazil-india-indonesia')
def compare_brazil_india_indonesia():
    return render_template("compare/brazil-india-indonesia.html")


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


@client_bp.route('/outcome')
def outcome():
    return render_template("outcome.html")


@client_bp.route('/scores')
def overall_scores():
    return render_template("scores.html")


@client_bp.route('/resources')
@login_required
def paper_resources():
    return render_template("paper-resources.html")


@client_bp.route('/api/v1/view/line/<idcode>')
def view_dynamic_line(idcode):
    return render_template("headless/dynamic-line.html", idcode=idcode)


@client_bp.route('/api/v1/view/overview')
def view_data_overview():
    return render_template("headless/data-overview.html")
