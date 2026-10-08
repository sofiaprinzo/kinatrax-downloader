from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    kinatrax_api_key: str
    kinatrax_base_url: str
    kinatrax_api_path: str
    kinatrax_remote_root: str
    kinatrax_local_raw_root: Path
    database_url: str
    ingest_log_table: str
    rate_limit_calls: int
    rate_limit_seconds: int
    max_retries: int


def load_settings() -> Settings:
    pass



