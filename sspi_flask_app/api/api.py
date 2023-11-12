from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required
from bson import json_util

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)