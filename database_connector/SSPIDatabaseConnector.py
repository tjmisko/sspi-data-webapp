from os import environ, path
import ssl
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry

class SSPIDatabase:
    def __init__(self):
        self.token = self.get_token()
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        self.session = requests.session()
        self.session.mount('https://', CustomHttpAdapter(ctx))
        self.login_session()
    
    def get_token(self):
        basedir = path.abspath(path.dirname(path.dirname(__file__)))
        load_dotenv(path.join(basedir, '.env'))
        return environ.get("APIKEY")
    
    def login_session(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        self.session.post("http://127.0.0.1:5000/remote/session/login", headers=headers, verify=False)

    def get(self, request_string):
        if request_string[0] == "/":
            request_string = request_string[1:]
        return self.session.get(f"http://127.0.0.1:5000/{request_string}")

class CustomHttpAdapter (requests.adapters.HTTPAdapter):
# "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)