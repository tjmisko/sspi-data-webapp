import logging
import os
import re

import pycountry
from flask import Blueprint, redirect, render_template, request, url_for
from flask import current_app as app
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf
from markdown import markdown

from sspi_flask_app.api.core.dashboard import (
    build_download_tree_structure,
    build_indicators_data,
    build_indicators_data_static,
)
from sspi_flask_app.api.resources.utilities import parse_json, public_databases
from sspi_flask_app.models.database import (
    sspi_custom_user_structure,
    sspi_metadata,
    sspidb,
)

client_bp = Blueprint(
    'client_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/client/static')

from sspi_flask_app.auth.decorators import admin_required

###########################
# SSPI DYNAMIC DATA PAGES #
###########################

@client_bp.route('/')
def home():
    pillar_category_tree = sspi_metadata.pillar_category_summary_tree()
    sspi_49_details = sspi_metadata.country_group_details("SSPI49")
    sspi_49_details.sort(key=lambda x: x["Metadata"]["Country"])
    sspi_extended_details = sspi_metadata.country_group_details("SSPIExtended")
    sspi_extended_details.sort(key=lambda x: x["Metadata"]["Country"])
    return render_template(
        "home.html",
        pillar_category_tree=pillar_category_tree,
        sspi_49_details=sspi_49_details,
        sspi_extended_details=sspi_extended_details,
    )


@client_bp.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@client_bp.route('/about')
def about():
    return render_template('about.html')


@client_bp.route('/countries')
def countries():
    sspi_49_details = sspi_metadata.country_group_details("SSPI49")
    sspi_49_details.sort(key=lambda x: x["Metadata"]["Country"])
    sspi_extended_details = sspi_metadata.country_group_details("SSPIExtended")
    sspi_extended_details.sort(key=lambda x: x["Metadata"]["Country"])
    return render_template(
        'countries.html',
        sspi_49_details=sspi_49_details,
        sspi_extended_details=sspi_extended_details,
    )


@client_bp.route('/methodology')
def methodology():
    return render_template('methodology.html')


@client_bp.route('/contact')
def contact():
    return render_template('contact.html')


@client_bp.route('/data')
def data():
    return render_template('data.html')

@client_bp.route('/data/overview')
def data_overview():
    return render_template("data-overview.html")


@client_bp.route('/customize')
def customize_home():
    """
    Landing page for customization feature.
    Shows information and directs users to login/register or builder based on auth status.
    """
    return render_template('customize/customize-home.html')

@client_bp.route('/customize/load')
def customize_load():
    """
    Load page for customization feature.
    Shows pre-built and saved configurations.
    Client-side JavaScript checks localStorage for active editing session.
    Works for both authenticated and anonymous users.
    """
    logger = logging.getLogger(__name__)
    # Check if user is authenticated
    is_authenticated = current_user.is_authenticated
    saved_configurations = []
    # Define prebuilt configurations
    prebuilt_configurations = [
        {
            'id': 'default',
            'name': 'Standard SSPI',
            'description': 'Standard SSPI structure with all 54 indicators across sustainability, material security, and public goods.',
            'pillars': 3,
            'categories': 18,
            'indicators': 54,
            'recommended': True
        }
    ]
    if is_authenticated:
        # Fetch saved configurations from database (authentication required)
        try:
            saved_configurations = sspi_custom_user_structure.list_config_names(
                username=current_user.username
            )
            logger.info(f"Loaded {len(saved_configurations)} configurations for user {current_user.username}")
        except Exception as e:
            logger.error(f"Error fetching configurations for user {current_user.username}: {e}")
            saved_configurations = []
    csrf_token = generate_csrf()
    return render_template(
        'customize/customize-load.html',
        is_authenticated=is_authenticated,
        prebuilt_configurations=prebuilt_configurations,
        saved_configurations=saved_configurations,
        csrf_token=csrf_token,
        title="Sign in to save custom configurations",
        subtitle=""
    )


@client_bp.route('/customize/builder')
def customize_configuration_builder():
    """
    Main customization builder interface.
    Client-side JavaScript checks localStorage for active editing session.
    Accessible to all users (authentication only required for saving).
    """
    csrf_token = generate_csrf()
    return render_template('customize/customization-builder.html',
                         csrf_token=csrf_token)


@client_bp.route('/customize/visualize/<config_id>')
def custom_visualization(config_id):
    """Production visualization page for custom SSPI configurations"""
    return render_template('customize/custom_visualization.html', config_id=config_id)


@client_bp.route('/customize/test-chart')
def test_custom_chart():
    """Test page for custom SSPI chart development and debugging"""
    return render_template('customize/test_custom_chart.html')


@client_bp.route('/data/country/<country_code>')
def country_data(country_code):
    country_code = country_code.upper()
    cdetail = sspi_metadata.get_country_detail(country_code)
    return render_template('country-data.html', cdetail=cdetail)


@client_bp.route('/data/dataset/<dataset_code>')
def dataset_data(dataset_code):
    dataset_code = dataset_code.upper()
    dataset_detail = sspi_metadata.get_dataset_detail(dataset_code)
    dataset_notes = sspi_metadata.get_dataset_documentation(dataset_code)
    return render_template('dataset-panel-data.html', dataset_detail=dataset_detail, dataset_notes_html=dataset_notes)


@client_bp.route('/data/indicator/<indicator_code>')
def indicator_data(indicator_code):
    indicator_code = indicator_code.upper()
    if indicator_code not in sspi_metadata.indicator_codes():
        return render_template(
            'score-panel-data.html',
            PanelItemCode=indicator_code,
            PanelItemType='Indicator',
            error=True
        )
    return render_template(
        'score-panel-data.html',
        PanelItemCode=indicator_code,
        PanelItemType='Indicator',
        methodology=sspi_metadata.get_item_methodology_html(indicator_code),
        error=False
    )


@client_bp.route('/data/category/<category_code>')
def category_data(category_code):
    category_code = category_code.upper()
    if category_code not in sspi_metadata.category_codes():
        return render_template(
            'score-panel-data.html',
            PanelItemCode=category_code,
            PanelItemType='Category',
            error=True
        )
    return render_template(
        'score-panel-data.html',
        PanelItemCode=category_code,
        PanelItemType='Category',
        methodology=sspi_metadata.get_item_methodology_html(category_code),
        error=False
    )


@client_bp.route('/data/pillar/<pillar_code>')
def pillar_data(pillar_code):
    pillar_code = pillar_code.upper()
    if pillar_code not in sspi_metadata.pillar_codes():
        return render_template(
            'score-panel-data.html',
            PanelItemCode=pillar_code,
            PanelItemType='Pillar',
            medhodology=sspi_metadata.get_item_methodology_html(pillar_code),
            error=True
        )
    return render_template(
        'score-panel-data.html',
        PanelItemCode=pillar_code,
        PanelItemType='Pillar',
        error=False
    )


@client_bp.route('/indicators')
def indicators():
    indicators_data = build_indicators_data()
    view_item = request.args.get("viewItem")
    return render_template('indicators.html', indicators_data=indicators_data, view_item=view_item)

@client_bp.route('/analysis')
def analysis():
    return render_template('analysis.html')

@client_bp.route('/analysis/<analysis_code>')
def analysis_page(analysis_code):
    analysis_code = analysis_code.upper()
    analysis_detail = sspi_metadata.get_analysis_detail(analysis_code)
    analysis_title = analysis_detail.get("AnalysisTitle")
    analysis_subtitle = analysis_detail.get("AnalysisSubtitle")
    analysis_date = analysis_detail.get("Date")
    analysis_authors = analysis_detail.get("Authors")
    analysis_html = sspi_metadata.get_analysis_html(analysis_code)
    return render_template(
        'analysis-template.html',
        title = analysis_title,
        subtitle = analysis_subtitle,
        authors = analysis_authors,
        date = analysis_date,
        analysis = analysis_html
    )


@client_bp.route('/download')
def download():
    # Filter public databases to only those that exist in the database
    databases = [db for db in public_databases if db["name"] in sspidb.list_collection_names()]
    indicator_tree = build_download_tree_structure()
    country_groups = sspi_metadata.country_groups()
    countries = []
    country_codes = sspi_metadata.country_group('SSPI67')
    for code in country_codes:
        try:
            country = pycountry.countries.get(alpha_3=code)
            if country:
                countries.append({
                    'code': code,
                    'name': country.name
                })
        except Exception:
            countries.append({
                'code': code,
                'name': code
            })
    countries.sort(key=lambda x: x['name'])
    return render_template('download.html', 
                           databases=databases,
                           indicator_tree=indicator_tree,
                           countries=countries,
                           country_groups=country_groups)

###############################
# SSPI 2018 STATIC DATA PAGES #
###############################

@client_bp.route('/2018')
def home_2018():
    return render_template("static/2018-home.html")


@client_bp.route('/2018/indicators')
def indicators_static():
    indicators_data = build_indicators_data_static()
    return render_template('static/2018-indicators.html', indicators_data=indicators_data)


@client_bp.route('/2018/scores')
def overall_scores_2018():
    return render_template("static/2018-scores.html")

@client_bp.route('/2018/data')
def overall_data_2018():
    return redirect(url_for('client_bp.overall_scores_2018'))

@client_bp.route('/2018/methodology')
def methodology_2018():
    return render_template('static/2018-methodology.html')


@client_bp.route('/2018/compare')
def compare_home_2018():
    return render_template("static/2018-compare-home.html")


@client_bp.route('/2018/data/indicator/<indicator_code>')
def indicator_data_2018(indicator_code):
    indicator_code = indicator_code.upper()
    return render_template('static/2018-item-static.html', item_code=indicator_code)


@client_bp.route('/2018/data/category/<category_code>')
def category_data_2018(category_code):
    category_code = category_code.upper()
    return render_template('static/2018-item-static.html', item_code=category_code)


@client_bp.route('/2018/data/pillar/<pillar_code>')
def pillar_data_2018(pillar_code):
    pillar_code = pillar_code.upper()
    return render_template('static/2018-item-static.html', item_code=pillar_code)


@client_bp.route('/2018/compare/custom', methods=['POST'])
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
        "html": render_template("static/compare/2018-comparison-result.html", comparison_list=comparison_list),
        "data": comparison_list
    })


@client_bp.route('/2018/compare/sweden-france-japan')
def compare_sweden_france_japan():
    return render_template("static/compare/sweden-france-japan.html")


@client_bp.route('/2018/compare/china-russia-usa')
def compare_china_russia_usa():
    return render_template("static/compare/china-russia-usa.html")


@client_bp.route('/2018/compare/brazil-india-indonesia')
def compare_brazil_india_indonesia():
    return render_template("static/compare/brazil-india-indonesia.html")


@client_bp.route('/2018/outcome')
def outcome():
    return render_template("static/2018-outcome.html")


@client_bp.route('/2018/resources')
@admin_required
def paper_resources():
    return render_template("/static/2018-paper-resources.html")


@client_bp.route('/map')
def world_map_page():
    return render_template("world-map.html")


@client_bp.route('/globe')
def globe_tree():
    return render_template("globe.html")


# @client_bp.route('/history')
# def project_history():
#     return render_template("history.html")


