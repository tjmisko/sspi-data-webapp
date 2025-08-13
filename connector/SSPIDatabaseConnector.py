from os import environ, path
import re
import ssl
import json
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
import urllib3
import logging

log = logging.getLogger(__name__)


class SSPIDatabaseConnector:
    def __init__(self):
        self.remote_token = self.get_token()
        self.local_token = self.get_token(token_name="SSPI_APIKEY_LOCAL")
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        self.local_session = requests.Session()
        self.local_session.mount('https://', LocalHttpAdapter(ctx))
        self.remote_session = requests.Session()
        self.login_session_local()
        self.login_session_remote()
        with open(path.join(path.dirname(path.dirname(__file__)), 'wsgi.py'), 'r') as f:
            contents = f.read().strip()
            result = re.search(r"port=(\d)+", contents)
            if result:
                self.local_port_number = result.group(1)
            else: 
                log.error("Could not find port number in wsgi.py!")
                self.local_port_number = "5000"
        self.local_port_number = "wsgi.py"
        self.local_base = f"http://127.0.0.1:{self.local_port_number}"
        self.remote_base = "https://sspi.world"

    def get_token(self, token_name="SSPI_APIKEY"):
        basedir = path.abspath(path.dirname(path.dirname(__file__)))
        load_dotenv(path.join(basedir, '.env'))
        key = environ.get(token_name)
        if key is None:
            log.error("No API key found in environment variables")
            raise ValueError("No API key found in environment variables")
        log.info("API key retrieval successful")
        return key

    def login_session_local(self):
        headers = {'Authorization': f'Bearer {self.local_token}'}
        self.local_session.headers.update(headers)

    def login_session_remote(self):
        headers = {'Authorization': f'Bearer {self.remote_token}'}
        self.remote_session.headers.update(headers)

    def call(self, request_string, method="GET", remote=False, stream=False, data=None, timeout=120):
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        if request_string[0] == "/":
            request_string = request_string[1:]
        endpoint = f"{base_url}/{request_string}"
        if method == "POST":
            if data:
                sesh.headers.update({'Content-Type': 'application/json'})
            return sesh.post(endpoint, stream=stream, json=data, timeout=timeout)
        if method == "DELETE":
            return sesh.delete(endpoint, stream=stream, timeout=timeout)
        return sesh.get(endpoint, stream=stream, timeout=timeout)

    def load(self, obs_lst: list[dict], database_name: str, indicator_code: str, remote=False) -> str:
        """
        Load a list of observations in JSON format into the database
        """
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        endpoint = f"{base_url}/api/v1/load/{database_name}/{indicator_code}"
        res = sesh.post(endpoint, json=json.dumps(obs_lst))
        return res


class LocalHttpAdapter(HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context
        )
