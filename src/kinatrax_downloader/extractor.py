from dataclasses import dataclass
from pathlib import Path
from kinatrax_downloader.explorer_api import ExplorerApi, ExplorerItem
from kinatrax_downloader.ingest_log import PostgresIngestLog


DATA_EXTENSIONS = {".csv", ".json", ".txt", ".tsv", ".xml"}
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"}


@dataclass
class KinaTraxExtractor:
    api: ExplorerApi
    ingest_log: PostgresIngestLog
    remote_root: str
    raw_root: Path

    def list_sessions(self, season: str | int) -> list[str]:
        pass

    def download_session(self, session_name: str) -> int:
        pass

    def download_new_sessions(self, season: str | int) -> dict[str, int]:
        pass

    def walk_session_files(self, folder_path: str) -> list[ExplorerItem]:
        pass

    def is_data_file(self, path: str) -> bool:
        pass


