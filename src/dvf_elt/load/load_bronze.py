import logging
from pathlib import Path

import psycopg

from dvf_elt.ingest.parse_dvf import parse_dvf_file

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"

INSERT_SQL = """
    INSERT INTO bronze_dvf
        (date_mutation, valeur_fonciere, code_commune, nom_commune,
         type_local, surface_reelle_bati, source_file)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

def load_file_to_bronze(csv_path: Path, quarantine_path: Path, batch_size: int = 5000) -> int:
    rows_loaded = 0
    batch = []

    with psycopg.connect(CONN_STR) as conn:
        with conn.cursor() as cur:
            for txn in parse_dvf_file(csv_path, quarantine_path):
                batch.append((
                    txn.date_mutation, txn.valeur_fonciere, txn.code_commune,
                    txn.nom_commune, txn.type_local, txn.surface_reelle_bati,
                    csv_path.name,
                ))
                if len(batch) >= batch_size:
                    cur.executemany(INSERT_SQL, batch)
                    rows_loaded += len(batch)
                    batch.clear()

            if batch:
                cur.executemany(INSERT_SQL, batch)
                rows_loaded += len(batch)

        conn.commit()

    log.info("loaded %d rows into bronze_dvf from %s", rows_loaded, csv_path.name)
    return rows_loaded