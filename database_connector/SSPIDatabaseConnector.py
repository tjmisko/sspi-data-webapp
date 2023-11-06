from os import environ, path
from dotenv import load_dotenv
import requests

class SSPIDatabaseConnector:
    def __init__(self):
        self.token = self.get_token()
        self.session = requests.Session()

    def get_token(self):
        basedir = path.abspath(path.dirname(path.dirname(__file__)))
        load_dotenv(path.join(basedir, '.env'))
        return environ.get("APIKEY")
    
    def login_session(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        self.session.get("https://127.0.0.1/remote/session/login", headers=headers)

    def request(self, request_string):
        return self.session.get(f"https://127.0.0.1{request_string}")

