from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExplorerItem:
    name: str
    path: str
    kind: str


@dataclass
class ExplorerApi:
    api_key: str
    base_url: str
    api_path: str
    rate_limit_calls: int
    rate_limit_seconds: int
    max_retries: int

    def list_folders_at(self, path: str) -> list[ExplorerItem]:
        pass

    def download_file(self, file_path: str, destination: Path) -> None:
        pass

    def wait_for_rate_limit(self) -> None:
        pass

    def request_with_retries(self, endpoint: str, payload: dict, stream: bool = False):
        pass




