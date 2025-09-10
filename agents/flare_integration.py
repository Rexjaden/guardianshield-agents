"""
flare_integration.py: Handles integration with Flare for multi-chain spam site info and metadata storage.
"""
import requests
import logging
import asyncio
import httpx

class FlareIntegration:
    async def async_post(self, endpoint, payload, headers=None, retries=3):
        url = f"{self.api_url}/{endpoint}"
        headers = headers or {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.status_code == 200
            except Exception as e:
                logging.error(f"Async POST error to {endpoint} (attempt {attempt+1}): {e}")
                await asyncio.sleep(2)
        return False

    async def async_get(self, endpoint, params=None, headers=None, retries=3):
        url = f"{self.api_url}/{endpoint}"
        headers = headers or {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    if isinstance(data, dict):
                        return data
                    else:
                        logging.warning(f"Unexpected response format from Flare async GET {endpoint}.")
                        return None
            except Exception as e:
                logging.error(f"Async GET error from {endpoint} (attempt {attempt+1}): {e}")
                await asyncio.sleep(2)
        return None

    def standardize_metadata(self, metadata):
        """
        Standardize metadata schema for consistency.
        """
        return {
            "id": metadata.get("id"),
            "type": metadata.get("type"),
            "timestamp": metadata.get("timestamp"),
            "source": metadata.get("source"),
            "details": metadata.get("details"),
            "incidents": metadata.get("incidents", []),
        }
    def __init__(self, api_url: str, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key

    def get_spam_site_info(self, query_params=None):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = requests.get(f"{self.api_url}/spam-sites", params=query_params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            else:
                logging.warning("Unexpected response format from Flare spam-sites API.")
                return None
        except Exception as e:
            logging.error(f"Error fetching spam site info: {e}")
            return None

    def update_dmer(self, dmer_data):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = requests.post(f"{self.api_url}/dmer/update", json=dmer_data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error updating DMER in Flare: {e}")
            return False

    def store_metadata(self, metadata):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        standardized = self.standardize_metadata(metadata)
        try:
            response = requests.post(f"{self.api_url}/metadata", json=standardized, headers=headers, timeout=10)
            response.raise_for_status()
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error storing metadata in Flare: {e}")
            return False

    def get_state_connector_data(self, query_params=None):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = requests.get(f"{self.api_url}/state-connector", params=query_params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            else:
                logging.warning("Unexpected response format from Flare state-connector API.")
                return None
        except Exception as e:
            logging.error(f"Error fetching state connector data: {e}")
            return None

    def verify_external_proof(self, proof_data):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = requests.post(f"{self.api_url}/state-connector/verify", json=proof_data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error verifying external proof in Flare: {e}")
            return False
