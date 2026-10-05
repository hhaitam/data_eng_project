import logging
from datetime import date, datetime, timezone
from pathlib import Path

import psycopg

from dvf_elt.load.load_bronze import load_file_to_bronze
from dvf_elt.load.load_silver import load_silver
from dvf_elt.load.load_gold import load_gold

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"

class PipelineError(Exception):
    """Raised when a pipeline stage fails; wraps the original error."""

def _start_execution(conn, source_file: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pipeline_executions (source_file, started_at) VALUES (%s, %s) RETURNING id",
            (source_file, datetime.now(timezone.utc)),
        )
        exec_id = cur.fetchone()[0]
    conn.commit()
    return exec_id

def _update_stage(conn, exec_id: int, stage: str, status: str, error_message: str | None = None):
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE pipeline_executions SET {stage}_status = %s, error_message = %s WHERE id = %s",
            (status, error_message, exec_id),
        )
    conn.commit()

def _finish_execution(conn, exec_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE pipeline_executions SET finished_at = %s WHERE id = %s",
            (datetime.now(timezone.utc), exec_id),
        )
    conn.commit()

def run_pipeline(csv_path: Path, quarantine_path: Path, as_of_date: date) -> int:
    source_file = csv_path.name
    conn = psycopg.connect(CONN_STR)
    exec_id = _start_execution(conn, source_file)
    log.info("pipeline execution %d started for %s", exec_id, source_file)

    try:
        rows = load_file_to_bronze(csv_path, quarantine_path)
        _update_stage(conn, exec_id, "bronze", "success")
        log.info("bronze: %d rows", rows)
    except Exception as e:
        _update_stage(conn, exec_id, "bronze", "failed", str(e))
        _finish_execution(conn, exec_id)
        conn.close()
        raise PipelineError(f"bronze stage failed: {e}") from e

    try:
        silver_rows = load_silver(source_file)
        _update_stage(conn, exec_id, "silver", "success")
        log.info("silver: %d rows", silver_rows)
    except Exception as e:
        _update_stage(conn, exec_id, "silver", "failed", str(e))
        _finish_execution(conn, exec_id)
        conn.close()
        raise PipelineError(f"silver stage failed: {e}") from e

    try:
        gold_rows = load_gold(as_of_date)
        _update_stage(conn, exec_id, "gold", "success")
        log.info("gold: %d rows", gold_rows)
    except Exception as e:
        _update_stage(conn, exec_id, "gold", "failed", str(e))
        _finish_execution(conn, exec_id)
        conn.close()
        raise PipelineError(f"gold stage failed: {e}") from e

    _finish_execution(conn, exec_id)
    conn.close()
    log.info("pipeline execution %d finished successfully", exec_id)
    return exec_id