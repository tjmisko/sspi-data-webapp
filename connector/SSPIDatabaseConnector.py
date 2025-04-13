from os import environ, path
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
        self.local_base = "http://127.0.0.1:5000"
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

    def call(self, request_string, method="GET", remote=False) -> requests.Response:
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        if request_string[0] == "/":
            request_string = request_string[1:]
        if method == "POST":
            return sesh.post(f"{base_url}/{request_string}")
        if method == "DELETE":
            return sesh.delete(f"{base_url}/{request_string}")
        return sesh.get(f"{base_url}/{request_string}")

    def collect(self, indicator_code: str, remote=False):
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        endpoint = f"{base_url}/api/v1/collect/{indicator_code}"
        with sesh.get(endpoint, stream=True) as res:
            for line in res.iter_lines(decode_unicode=True):
                yield line

    def finalize(self, remote=False, special=""):
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        endpoint = f"{base_url}/api/v1/production/finalize"
        if special:
            endpoint += special
        with sesh.get(endpoint, stream=True) as res:
            for line in res.iter_lines(decode_unicode=True):
                yield line

    def load(self, obs_lst: list[dict], database_name: str, indicator_code: str, remote=False) -> str:
        """
        Load a list of observations in JSON format into the database
        """
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        endpoint = f"{base_url}/api/v1/load/{database_name}/{indicator_code}",
        # - [ ] Check on whether verify=False should be inserted here programatically
        res = sesh.post(endpoint, json=json.dumps(obs_lst))
        msg = f"Load Request Returned with Status Code {res.status_code}"
        log.info(msg)
        return str(res.text)

    def delete_indicator_data(self, database_name: str, indicator_code: str, remote=False) -> str:
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        endpoint = f"{base_url}/api/v1/delete/indicator/{database_name}/{indicator_code}"
        res = sesh.delete(endpoint)
        msg_1 = f"Delete Request Returned with Status Code {res.status_code}\n"
        msg_2 = str(res.text)
        log.info(msg_1)
        return msg_1 + msg_2

    def delete_duplicate_data(self, database_name: str, remote=False) -> str:
        sesh = self.remote_session if remote else self.local_session
        base_url = self.remote_base if remote else self.local_base
        endpoint = f"{base_url}/api/v1/delete/duplicates"
        data = {"database": database_name}
        res = sesh.post(endpoint, data=data)
        msg = f"Delete Request Returned with Status Code {res.status_code}"
        log.info(msg)
        return str(res.text)


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
