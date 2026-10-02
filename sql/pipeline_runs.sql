CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    rows_loaded INT NOT NULL,
    status TEXT NOT NULL,           -- 'success' or 'failed'
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL
);