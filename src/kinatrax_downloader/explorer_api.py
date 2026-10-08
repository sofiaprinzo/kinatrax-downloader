from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExplorerItem:
    name: str #
    path: str
    kind: str #folder or file


@dataclass
class ExplorerApi:
    api_key: str
    base_url: str
    api_path: str
    rate_limit_calls: int
    rate_limit_seconds: int
    max_retries: int

    # Pass in season as parameter and return a list of all files listed under that season
    def list_folders_at(self, path: str) -> list[ExplorerItem]:
        season = str(path).strip("/")
        url = f"{base_url}/{api_path}/list_folders_at"
        payload = {"access_token": api_key, "path": path}
        response = requests.post(url, data=payload)
        response.raise_for_status()
        data = response.json()

        folders = []

        for folder in data["folders"]:
            folders.append(ExplorerItem(f"{season}_Folder", str(folder), "folder"))

        return folders



    def download_file(self, file_path: str, destination: Path) -> None:
        pass

    def wait_for_rate_limit(self) -> None:
        pass

    def request_with_retries(self, endpoint: str, payload: dict, stream: bool = False):
        pass
