from datetime import date
import pytest
import psycopg

from dvf_elt.load.load_gold import load_gold, CONN_STR

pytestmark = pytest.mark.integration

def test_gold_transaction_counts_match_silver():
    as_of = date(2025, 1, 1)
    load_gold(as_of)

    with psycopg.connect(CONN_STR) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT coalesce(sum(nb_transactions), 0)
            FROM gold_commune_yearly_stats
            WHERE year = %s
        """, (as_of.year,))
        gold_total = cur.fetchone()[0]

        cur.execute("""
            SELECT count(*)
            FROM silver_dvf
            WHERE EXTRACT(YEAR FROM date_mutation) = %s
              AND prix_m2 IS NOT NULL
        """, (as_of.year,))
        silver_total = cur.fetchone()[0]

    assert gold_total == silver_total