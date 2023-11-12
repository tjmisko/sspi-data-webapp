from os import environ, path
from dotenv import load_dotenv
import requests

class SSPIDatabase:
    def __init__(self):
        self.token = environ.get("APIKEY")

    def print_token(self):
        print(environ.get("APIKEY"))
        print(self.token)
    
    def get_token(self):
        basedir = path.abspath(path.dirname(__file__))
        print(basedir)
        load_dotenv(path.join(basedir, '.env'))
        print(environ.get("APIKEY"))
        return environ.get("APIKEY")

