import logging
from datetime import date
from pathlib import Path

import psycopg
from psycopg import ClientCursor

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"
SQL_PATH = Path("sql/transform_silver_to_gold.sql")

def load_gold(as_of_date: date) -> int:
    sql = SQL_PATH.read_text()
    with psycopg.connect(CONN_STR, cursor_factory=ClientCursor) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"as_of_date": as_of_date})
            cur.execute(
                "SELECT count(*) FROM gold_commune_yearly_stats WHERE year = %s",
                (as_of_date.year,),
            )
            count = cur.fetchone()[0]
        conn.commit()
    log.info("gold_commune_yearly_stats now has %d rows for year %d", count, as_of_date.year)
    return count