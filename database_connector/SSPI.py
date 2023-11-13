import os
import requests

class SSPIDatabase:
    def __init__(self):
        self.token = os.environ.get("SSPI_TOKEN")
    
    def get_data(self):
        requests.get()
        return 