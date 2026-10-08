CREATE SCHEMA IF NOT EXISTS staging_level;

CREATE TABLE IF NOT EXISTS staging_level.kinatrax_ingest_log (
    ingest_id PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    session_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    s3_path TEXT NOT NULL,
    local_path TEXT,
    file_count INTEGER NOT NULL DEFAULT 0,
    downloaded_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('downloaded', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS

