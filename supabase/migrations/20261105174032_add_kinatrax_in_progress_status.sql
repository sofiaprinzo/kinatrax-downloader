BEGIN;

ALTER TABLE public.kinatrax_ingest_log
DROP CONSTRAINT kinatrax_ingest_log_status_check;

ALTER TABLE public.kinatrax_ingest_log
ADD CONSTRAINT kinatrax_ingest_log_status_check
CHECK (status IN ('in_progress', 'downloaded', 'failed'));

COMMIT;
