from pathlib import Path


def normalize_s3_path(path: str) -> str:
    pass


def build_season_path(remote_root: str, season: str | int) -> str:
    pass


def session_name_from_path(session_path: str) -> str:
    pass


def season_from_session_name(session_name: str) -> str:
    pass


def build_session_path(remote_root: str, session_name: str) -> str:
    pass


def build_local_session_dir(raw_root: Path, session_name: str) -> Path:
    pass


def relative_path_in_session(file_path: str, session_path: str) -> Path:
    pass


def build_local_file_path(local_session_dir: Path, relative_file_path: Path) -> Path:
    pass





































