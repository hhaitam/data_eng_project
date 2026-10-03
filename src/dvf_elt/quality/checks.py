import logging
from dataclasses import dataclass

import psycopg

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"

@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str

def check_no_negative_or_zero_prices(conn) -> CheckResult:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM silver_dvf WHERE valeur_fonciere <= 0")
        bad = cur.fetchone()[0]
    return CheckResult(
        "no_negative_or_zero_prices",
        bad == 0,
        f"{bad} rows with valeur_fonciere <= 0",
    )

def check_no_nulls_in_required_columns(conn) -> CheckResult:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT count(*) FROM silver_dvf
            WHERE date_mutation IS NULL OR code_commune IS NULL OR valeur_fonciere IS NULL
        """)
        bad = cur.fetchone()[0]
    return CheckResult(
        "no_nulls_in_required_columns",
        bad == 0,
        f"{bad} rows with a null in a required column",
    )

def check_row_count_not_suspiciously_low(conn, min_expected: int = 1000) -> CheckResult:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM silver_dvf")
        total = cur.fetchone()[0]
    return CheckResult(
        "row_count_not_suspiciously_low",
        total >= min_expected,
        f"{total} rows (minimum expected: {min_expected})",
    )

def run_all_checks() -> list[CheckResult]:
    with psycopg.connect(CONN_STR) as conn:
        results = [
            check_no_negative_or_zero_prices(conn),
            check_no_nulls_in_required_columns(conn),
            check_row_count_not_suspiciously_low(conn),
        ]
    for r in results:
        level = logging.INFO if r.passed else logging.ERROR
        log.log(level, "[%s] %s — %s", "PASS" if r.passed else "FAIL", r.name, r.detail)
    return results