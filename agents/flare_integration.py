"""
flare_integration.py: Handles integration with Flare for multi-chain spam site info and metadata storage.
"""
import requests

class FlareIntegration:
    def __init__(self, api_url: str, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key

    def get_spam_site_info(self, query_params=None):
        # Example: Fetch multi-chain spam site info from Flare
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = requests.get(f"{self.api_url}/spam-sites", params=query_params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def update_dmer(self, dmer_data):
        # Example: Update DMER info in Flare
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = requests.post(f"{self.api_url}/dmer/update", json=dmer_data, headers=headers)
        return response.status_code == 200

    def store_metadata(self, metadata):
        # Example: Store metadata in Flare
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = requests.post(f"{self.api_url}/metadata", json=metadata, headers=headers)
        return response.status_code == 200
