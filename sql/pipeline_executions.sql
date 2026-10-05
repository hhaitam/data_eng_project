CREATE TABLE IF NOT EXISTS pipeline_executions (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    bronze_status TEXT NOT NULL DEFAULT 'pending',
    silver_status TEXT NOT NULL DEFAULT 'pending',
    gold_status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ
);