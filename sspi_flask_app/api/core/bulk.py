from flask import Blueprint, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.wid import bulkCollectWIDData


bulk_bp = Blueprint("bulk_bp", __name__,
                    template_folder="templates",
                    static_folder="static",
                    url_prefix="/bulk")


@bulk_bp.route("/collect/WID", methods=['GET'])
@login_required
def collect_wid():
    def collect_iterator(**kwargs):
        yield from bulkCollectWIDData(**kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')
