import logging
from datetime import datetime, timezone
from pathlib import Path

import psycopg

from dvf_elt.ingest.parse_dvf import parse_dvf_file

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"

DELETE_SQL = "DELETE FROM bronze_dvf WHERE source_file = %s"

INSERT_SQL = """
    INSERT INTO bronze_dvf
        (date_mutation, valeur_fonciere, code_commune, nom_commune,
         type_local, surface_reelle_bati, source_file)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

RUN_LOG_SQL = """
    INSERT INTO pipeline_runs
        (source_file, rows_loaded, status, started_at, finished_at)
    VALUES (%s, %s, %s, %s, %s)
"""

def load_file_to_bronze(csv_path: Path, quarantine_path: Path, batch_size: int = 5000) -> int:
    started_at = datetime.now(timezone.utc)
    source_file = csv_path.name
    rows_loaded = 0
    batch = []

    with psycopg.connect(CONN_STR) as conn:
        try:
            with conn.cursor() as cur:
                # Step A: wipe anything previously loaded from this same file
                cur.execute(DELETE_SQL, (source_file,))

                # Step B: insert fresh
                for txn in parse_dvf_file(csv_path, quarantine_path):
                    batch.append((
                        txn.date_mutation, txn.valeur_fonciere, txn.code_commune,
                        txn.nom_commune, txn.type_local, txn.surface_reelle_bati,
                        source_file,
                    ))
                    if len(batch) >= batch_size:
                        cur.executemany(INSERT_SQL, batch)
                        rows_loaded += len(batch)
                        batch.clear()

                if batch:
                    cur.executemany(INSERT_SQL, batch)
                    rows_loaded += len(batch)

                # Step C: log success
                finished_at = datetime.now(timezone.utc)
                cur.execute(RUN_LOG_SQL, (source_file, rows_loaded, "success", started_at, finished_at))

            conn.commit()  # delete + inserts + run log all saved together, or none of them are

        except Exception:
            conn.rollback()
            finished_at = datetime.now(timezone.utc)
            with psycopg.connect(CONN_STR) as log_conn:
                with log_conn.cursor() as log_cur:
                    log_cur.execute(RUN_LOG_SQL, (source_file, 0, "failed", started_at, finished_at))
                log_conn.commit()
            log.exception("load failed for %s", source_file)
            raise

    log.info("loaded %d rows into bronze_dvf from %s", rows_loaded, source_file)
    return rows_loaded