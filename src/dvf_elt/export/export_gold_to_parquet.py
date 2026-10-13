import logging
from pathlib import Path

import pandas as pd
import psycopg

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"

def export_gold_to_parquet(year: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"commune_yearly_stats_{year}.parquet"

    with psycopg.connect(CONN_STR) as conn:
        df = pd.read_sql(
            "SELECT * FROM gold_commune_yearly_stats WHERE year = %(year)s",
            conn,
            params={"year": year},
        )

    df.to_parquet(out_path, index=False, engine="pyarrow")
    log.info("exported %d rows to %s", len(df), out_path)
    return out_path