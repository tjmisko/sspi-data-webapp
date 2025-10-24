from flask import Blueprint, render_template, request, current_app as app
import os
from markdown import markdown
from flask_login import login_required
import re
import pycountry
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.models.database import sspi_metadata, sspidb
from sspi_flask_app.api.core.dashboard import build_indicators_data


def build_download_tree_structure():
    """
    Build hierarchical tree structure for download form indicator selector.
    Similar to build_indicators_data() but simplified for form use.
    
    Returns:
        dict: Tree structure with SSPI -> Pillars -> Categories -> Indicators
    """
    try:
        # Get all item details
        all_items = sspi_metadata.item_details()
        
        if not all_items:
            return {"error": "No metadata items found"}
        
        # Organize items by type and code
        items_by_type = {
            'SSPI': [],
            'Pillar': [],
            'Category': [],
            'Indicator': []
        }
        
        items_by_code = {}
        
        for item in all_items:
            item_type = item.get('ItemType', 'Unknown')
            item_code = item.get('ItemCode', '')
            
            if item_type in items_by_type:
                items_by_type[item_type].append(item)
            
            if item_code:
                items_by_code[item_code] = item
        
        # Start with SSPI root
        sspi_items = items_by_type.get('SSPI', [])
        if not sspi_items:
            return {"error": "No SSPI root item found"}
        
        sspi_item = sspi_items[0]  # Should only be one SSPI item
        
        # Build tree structure recursively
        def build_node(item, level=0):
            node = {
                'itemCode': item.get('ItemCode', ''),
                'itemName': item.get('ItemName', item.get('ItemCode', '')),
                'itemType': item.get('ItemType', 'Unknown'),
                'level': level,
                'children': []
            }
            
            # Get children codes
            children_codes = item.get('Children', [])
            
            for child_code in children_codes:
                child_item = items_by_code.get(child_code)
                if child_item:
                    child_node = build_node(child_item, level + 1)
                    node['children'].append(child_node)
            
            # Sort children by ItemOrder if available, then by name
            node['children'].sort(key=lambda x: (
                items_by_code.get(x['itemCode'], {}).get('ItemOrder', 999),
                x['itemName']
            ))
            
            return node
        
        tree_structure = build_node(sspi_item)
        
        return tree_structure
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error building download tree structure: {str(e)}")
        return {"error": f"Error building tree structure: {str(e)}"}


client_bp = Blueprint(
    'client_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/client/static'
)


@client_bp.route('/')
def home():
    pillar_category_tree = sspi_metadata.pillar_category_summary_tree()
    return render_template('home.html', pillar_category_tree=pillar_category_tree)


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

@client_bp.route('/customize')
def customize():
    return render_template('customize.html')


@client_bp.route('/customize/visualize/<config_id>')
def custom_visualization(config_id):
    """Production visualization page for custom SSPI configurations"""
    return render_template('custom_visualization.html', config_id=config_id)


@client_bp.route('/customize/test-chart')
def test_custom_chart():
    """Test page for custom SSPI chart development and debugging"""
    return render_template('test_custom_chart.html')


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
    # Get structured data using the new backend function
    indicators_data = build_indicators_data()
    
    return render_template('indicators.html', 
                         indicators_data=indicators_data)


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


@client_bp.route('/static/scores')
def overall_scores():
    return render_template("static-scores.html")


@client_bp.route('/resources')
@login_required
def paper_resources():
    return render_template("paper-resources.html")


@client_bp.route('/api/v1/view/overview')
def view_data_overview():
    return render_template("headless/data-overview.html")


@client_bp.route('/download')
def download():
    # Get available databases, indicators, countries, and country groups
    # Only expose specific databases for download
    allowed_databases = [
        'sspi_score_data',
        'sspi_indicator_data', 
        'sspi_clean_api_data',
        'sspi_main_data_v3'
    ]
    databases = [db for db in allowed_databases if db in sspidb.list_collection_names()]
    
    # Build hierarchical tree structure for indicator selection
    indicator_tree = build_download_tree_structure()
    
    country_groups = sspi_metadata.country_groups()
    
    # Get countries with proper formatting (using SSPI67 as default country list)
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
            # If pycountry doesn't have the country, just use the code
            countries.append({
                'code': code,
                'name': code
            })
    
    # Sort countries by name
    countries.sort(key=lambda x: x['name'])
    
    return render_template('download.html', 
                         databases=databases,
                         indicator_tree=indicator_tree,
                         countries=countries,
                         country_groups=country_groups)
