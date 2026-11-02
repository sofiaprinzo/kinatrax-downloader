ALTER TABLE public.kinatrax_ingest_log
ADD COLUMN discovery_state JSONB,
ADD COLUMN transfer_state JSONB;
