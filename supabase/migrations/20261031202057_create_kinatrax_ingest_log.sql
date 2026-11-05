BEGIN;

CREATE TABLE public.kinatrax_ingest_log (
    session_name TEXT PRIMARY KEY,
    s3_path TEXT NOT NULL,
    file_count INTEGER CHECK (file_count >= 0),
    downloaded_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('downloaded', 'failed'))
);

ALTER TABLE public.kinatrax_ingest_log ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.kinatrax_ingest_log TO service_role;

COMMIT;
