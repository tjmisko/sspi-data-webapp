import logging
import sys

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/sspi.world/lib64/python3.9/site-packages")
sys.path.insert(0, '/var/www/sspi.world/flask_app')
from flask_app import app as application
application.secret_key = 'anything you wish'
