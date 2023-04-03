from ....source_utilities.sdg import collectSDGIndicatorData
from ....api import api_bp

@api_bp.route("/collect/biodiversity")
def collect_biodiversity():
    data = collectSDGIndicatorData("15.5.1")
    return str(type(data))