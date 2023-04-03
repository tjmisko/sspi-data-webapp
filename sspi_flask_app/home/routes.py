from flask import Blueprint, render_template
from flask import current_app as app
from flask_login import login_required

home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)

@home_bp.route('/')
def home():
    return render_template('home.html')

@home_bp.route('/about')
def about():
    return render_template('about.html')

@home_bp.route('/contact')
def contact():
    return render_template('contact.html')

@home_bp.route('/data')
def data():
    return render_template('data.html')

@home_bp.route('/indicators')
def indicators():
    return render_template('indicators.html')