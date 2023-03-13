from flask import Blueprint, render_template
from flask import current_app as app
from flask_login import login_required

home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static'
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

@home_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')