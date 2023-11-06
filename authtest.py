import urllib3
import requests
import ssl
from os import environ
from database_connector.SSPIDatabaseConnector import SSPIDatabaseConnector


# remote_session = get_legacy_session()
# remote_session.post("http://127.0.0.1:5000/remote/session/login", data=dict(username=environ.get("USERNAME"), password=environ.get("PASSWORD")))

database = SSPIDatabaseConnector()