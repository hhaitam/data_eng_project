from pathlib import Path
import pytest

from dvf_elt.load.load_bronze import load_file_to_bronze, CONN_STR
import psycopg

pytestmark = pytest.mark.integration  # marks this as needing a real DB

def test_loading_same_file_twice_does_not_duplicate_rows():
    csv_path = Path("data/raw/dvf_2025.csv.gz")
    quarantine_path = Path("data/quarantine/dvf_2025.log")

    n1 = load_file_to_bronze(csv_path, quarantine_path)
    n2 = load_file_to_bronze(csv_path, quarantine_path)

    assert n1 == n2

    with psycopg.connect(CONN_STR) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM bronze_dvf WHERE source_file = %s", (csv_path.name,))
        count = cur.fetchone()[0]

    assert count == n2