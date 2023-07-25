from source_utilities.iea import collect_IEA_indicator_data
from ...api import api_bp
from flask_login import current_user, login_required

@api_bp.route('/collect/indicator=TESbySource')
@login_required
def collect():
    data = collect_IEA_indicator_data('TESbySource')
    return str(type(data))
