from dataclasses import dataclass


@dataclass(frozen=True)
class IngestLogEntry:
    session_name: str
    season: int
    s3_path: str
    local_path: str
    file_count: int
    status: str
    error_message: str | None = None


@dataclass
class PostgresIngestLog:
    database_url: str
    table_name: str

    def ensure_table(self) -> None:
        pass

    def already_downloaded(self, session_path: str) -> bool:
        pass

    def mark_downloaded(self, entry: IngestLogEntry) -> None:
        pass

    def mark_failed(self, entry: IngestLogEntry) -> None:
        pass







