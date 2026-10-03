import logging
from pathlib import Path

import psycopg
from psycopg import ClientCursor

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"
SQL_PATH = Path("sql/transform_bronze_to_silver.sql")

def load_silver(source_file: str) -> int:
    sql = SQL_PATH.read_text()
    with psycopg.connect(CONN_STR, cursor_factory=ClientCursor) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"source_file": source_file})
            cur.execute(
                "SELECT count(*) FROM silver_dvf WHERE source_file = %s",
                (source_file,),
            )
            count = cur.fetchone()[0]
        conn.commit()
    log.info("silver_dvf now has %d rows for %s", count, source_file)
    return count