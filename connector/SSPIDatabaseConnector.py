from os import environ, path
import ssl
import json
from dotenv import load_dotenv
import pandas as pd
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

    def call_local(self, request_string, request_method="GET"):
        if request_string[0] == "/":
            request_string = request_string[1:]
        if request_method == "POST":
            return self.local_session.post(f"http://127.0.0.1:5000/{request_string}")
        if request_method == "DELETE":
            return self.local_session.delete(f"http://127.0.0.1:5000/{request_string}")
        return self.local_session.get(f"http://127.0.0.1:5000/{request_string}")

    def call_remote(self, request_string, request_method="GET"):
        if request_string[0] == "/":
            request_string = request_string[1:]
        if request_method == "POST":
            return self.remote_session.post(f"https://sspi.world/{request_string}")
        if request_method == "DELETE":
            return self.remote_session.delete(f"https://sspi.world/{request_string}")
        return self.remote_session.get(f"https://sspi.world/{request_string}")

    def get_data_local(self, request_string):
        if request_string[0] == "/":
            request_string = request_string[1:]
        return self.local_session.get(f"http://127.0.0.1:5000/{request_string}")

    def get_data_remote(self, request_string):
        if request_string[0] == "/":
            request_string = request_string[1:]
        return self.remote_session.get(f"https://sspi.world/{request_string}")

    def collect_data_local(self, indicator_code):
        endpoint = f"http://127.0.0.1:5000/api/v1/collect/{indicator_code}"
        with self.local_session.get(endpoint, stream=True) as res:
            for line in res.iter_lines(decode_unicode=True):
                yield line

    def collect_data_remote(self, indicator_code):
        endpoint = f"https://sspi.world/api/v1/collect/{indicator_code}"
        with self.remote_session.get(endpoint, stream=True) as res:
            for line in res.iter_lines(decode_unicode=True):
                yield line

    def finalize_data_local(self, special=""):
        endpoint = "http://127.0.0.1:5000/api/v1/production/finalize"
        if special:
            endpoint += special
            res = self.local_session.get(endpoint)
            return res.text
        else:
            with self.local_session.get(endpoint, stream=True) as res:
                for line in res.iter_lines(decode_unicode=True):
                    yield line

    def finalize_data_remote(self, special=""):
        endpoint = "https://sspi.world/api/v1/production/finalize"
        if special:
            endpoint += special
            res = self.remote_session.get(endpoint)
            return res.text
        else:
            with self.remote_session.get(endpoint, stream=True) as res:
                for line in res.iter_lines(decode_unicode=True):
                    yield line

    # - [ ] Decide what to do with this method
    def load_dataframe_local(self, dataframe: pd.DataFrame, IndicatorCode):
        pass
        # observations_list = dataframe.to_json(orient="records")
        # print(observations_list)
        # headers = {'Authorization': f'Bearer {self.token}'}
        # return self.local_session.post(
        #     f"http://127.0.0.1:5000/api/v1/load/{IndicatorCode}",
        #     headers=headers,
        #     json=observations_list,
        #     verify=False
        # )

    # - [ ] Decide what to do with this method
    def load_dataframe_remote(self, dataframe: pd.DataFrame, IndicatorCode):
        pass
        # observations_list = dataframe.to_json(orient="records")
        # headers = {'Authorization': f'Bearer {self.token}'}
        # print(f"Sending data: {observations_list}")
        # response = self.remote_session.post(
        #     f"https://sspi.world/api/v1/load/{IndicatorCode}",
        #     headers=headers,
        #     json=observations_list
        # )
        # print(response.text)
        # print(response.status_code)
        # return response

    def load_json_local(self, observations_list: list[dict], database_name: str,
                        IndicatorCode: str):
        """
        Load a list of observations in JSON format into the local database
        """
        response = self.local_session.post(
            f"http://127.0.0.1:5000/api/v1/load/{
                database_name}/{IndicatorCode}",
            json=json.dumps(observations_list),
            verify=False
        )
        log.info(f"Remote Load Request Returned with Status Code {
                 response.status_code}")
        return response

    def load_json_remote(self, observations_list: list[dict], database_name: str,
                         IndicatorCode: str):
        response = self.remote_session.post(
            f"https://sspi.world/api/v1/load/{database_name}/{IndicatorCode}",
            json=json.dumps(observations_list)
        )
        log.info(f"Remote Load Request Returned with Status Code {
                 response.status_code}")
        return response

    def delete_indicator_data_local(self, database_name: str, IndicatorCode: str):
        log.debug("Headers for Local Delete: " +
                  str(self.local_session.headers))
        response = self.local_session.delete(
            f"http://127.0.0.1:5000/api/v1/delete/indicator/{
                database_name}/{IndicatorCode}",
        )
        log.info(f"Local Delete Request Returned with Status Code {
                 response.status_code}")
        return response

    def delete_indicator_data_remote(self, database_name: str, IndicatorCode: str):
        response = self.remote_session.delete(
            f"https://sspi.world/api/v1/delete/indicator/{
                database_name}/{IndicatorCode}",
        )
        log.info(f"Remote Delete Request Returned with Status Code {
                 response.status_code}")
        return response

    def logout_local(self):
        self.local_session.get("http://127.0.0.1:5000/logout")

    def logout_remote(self):
        self.remote_session.get("https://sspi.world/logout")


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
