from flask import Blueprint, render_template, request, current_app as app
import os
from markdown import markdown
from flask_login import login_required
import re
import pycountry
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.models.database import sspi_metadata, sspidb
from sspi_flask_app.api.core.dashboard import build_indicators_data, build_download_tree_structure, build_indicators_data_static


client_bp = Blueprint(
    'client_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/client/static'
)

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
def customize():
    return render_template('customize.html')


@client_bp.route('/data/country/<CountryCode>')
def country_data(CountryCode):
    return render_template('country-data.html', CountryCode=CountryCode)


@client_bp.route('/data/indicator/<IndicatorCode>')
def indicator_data(IndicatorCode):
    IndicatorCode = IndicatorCode.upper()
    if IndicatorCode not in sspi_metadata.indicator_codes():
        return render_template(
            'score-panel-data.html',
            PanelItemCode=IndicatorCode,
            PanelItemType='Indicator',
            error=True
        )
    return render_template(
        'score-panel-data.html',
        PanelItemCode=IndicatorCode,
        PanelItemType='Indicator',
        methodology=sspi_metadata.get_item_methodology_html(IndicatorCode),
        error=False
    )


@client_bp.route('/data/category/<CategoryCode>')
def category_data(CategoryCode):
    CategoryCode = CategoryCode.upper()
    if CategoryCode not in sspi_metadata.category_codes():
        return render_template(
            'score-panel-data.html',
            PanelItemCode=CategoryCode,
            PanelItemType='Category',
            error=True
        )
    return render_template(
        'score-panel-data.html',
        PanelItemCode=CategoryCode,
        PanelItemType='Category',
        methodology=sspi_metadata.get_item_methodology_html(CategoryCode),
        error=False
    )


@client_bp.route('/data/pillar/<PillarCode>')
def pillar_data(PillarCode):
    PillarCode = PillarCode.upper()
    if PillarCode not in sspi_metadata.pillar_codes():
        return render_template(
            'score-panel-data.html',
            PanelItemCode=PillarCode,
            PanelItemType='Pillar',
            medhodology=sspi_metadata.get_item_methodology_html(PillarCode),
            error=True
        )
    return render_template(
        'score-panel-data.html',
        PanelItemCode=PillarCode,
        PanelItemType='Pillar',
        error=False
    )


@client_bp.route('/indicators')
def indicators():
    indicators_data = build_indicators_data()
    return render_template('indicators.html', indicators_data=indicators_data)

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
    allowed_databases = [
        'sspi_score_data',
        'sspi_indicator_data', 
        'sspi_clean_api_data',
        'sspi_main_data_v3'
    ]
    databases = [db for db in allowed_databases if db in sspidb.list_collection_names()]
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
        except:
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


@client_bp.route('/2018/methodology')
def methodology_2018():
    return render_template('static/2018-methodology.html')


@client_bp.route('/2018/compare')
def compare_home_2018():
    return render_template("static/2018-compare-home.html")


@client_bp.route('/2018/data/indicator/<IndicatorCode>')
def indicator_data_2018(IndicatorCode):
    IndicatorCode = IndicatorCode.upper()
    return render_template('2018-indicator-static.html')


@client_bp.route('/2018/data/category/<CategoryCode>')
def category_data_2018(CategoryCode):
    CategoryCode = CategoryCode.upper()
    return render_template('2018-category-static.html')



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
        "html": render_template("static/compare/comparison-result.html", comparison_list=comparison_list),
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
@login_required
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


