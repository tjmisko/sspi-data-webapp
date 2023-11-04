from flask import Blueprint, render_template, request
from flask_login import login_required
from wtforms import Form, StringField, SelectField, validators
from ..api.core.download import ClientDownloadForm


client_bp = Blueprint(
    'client_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)

@client_bp.route('/')
def home():
    return render_template('home.html')

@client_bp.route('/about')
def about():
    return render_template('about.html')

@client_bp.route('/contact')
def contact():
    return render_template('contact.html')

@client_bp.route('/data')
def data():
    download_form = ClientDownloadForm()
    return render_template('data.html', download_form=download_form)

@client_bp.route('/indicators')
def indicators():
    return render_template('indicators.html')

@client_bp.route('/methodology')
def methodology():
    return render_template('methodology.html')

@client_bp.route('/widget/<widgettype>')
def make_widget(widgettype):
    return render_template("data-widget.html", widgettype=widgettype)