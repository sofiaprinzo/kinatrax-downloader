# Handles authenticated requests to Explorer and folder listings

import time
from pathlib import PurePosixPath

import requests


REQUEST_INTERVAL = 6.1  # Account limit says 5 calls per 30 seconds, added +0.1s for safety
REQUEST_TIMEOUT = 30


class ExplorerClient:
    def __init__(self, api_key: str, base_url: str, http: requests.Session):
        self.api_key = api_key.strip()
        if not self.api_key:
            raise ValueError("Set KINATRAX_API_KEY in .env before running")
        self.base_url = base_url.rstrip("/")
        self.http = http
        self.last_request = None

    # Pace the query calls to be consistent with request interval
    # Will add failure retries later
    def request(self, endpoint: str, **parameters) -> requests.Response:
        if self.last_request is not None:
            elapsed = time.monotonic() - self.last_request
            remaining_wait = REQUEST_INTERVAL - elapsed
            if remaining_wait > 0:
                time.sleep(remaining_wait)
        self.last_request = time.monotonic()

        response = self.http.post(
            f"{self.base_url}/ktx_s3/{endpoint}", data={"access_token": self.api_key, **parameters},
            timeout=REQUEST_TIMEOUT, allow_redirects=False,
        )
        try:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError(f"Expected HTTP 200; received {response.status_code}.")
        except Exception:
            response.close()
            raise
        return response


    # Fetch the folders and files directly inside the requested path
    # Return their listing and file metadata without entering subfolders yet
    def list_folder(self, path: str) -> dict:
        with self.request("list_folders_at", path=path) as response:
            listing = response.json()

        if not isinstance(listing, dict):
            raise TypeError(f"Expected a dictionary for folder listing, but received {type(listing).__name__}.")
        
        missing_keys = {"folders", "files", "metadata", "has_more"} - listing.keys()
        if missing_keys:
            raise ValueError(f"Missing listing fields: {', '.join(sorted(missing_keys))}")
            
        return listing
