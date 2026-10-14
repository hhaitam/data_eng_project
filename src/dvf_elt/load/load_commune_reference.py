import logging
from datetime import datetime, timezone

import psycopg

from dvf_elt.ingest.geo_api import fetch_all_communes, fetch_commune, GeoApiError

log = logging.getLogger(__name__)

CONN_STR = "host=localhost port=5432 dbname=dvf user=dvf_user password=dvf_pass"

UPSERT_SQL = """
    INSERT INTO commune_reference
        (code_commune, nom, population, code_departement, code_region, fetched_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (code_commune) DO UPDATE SET
        nom = EXCLUDED.nom,
        population = EXCLUDED.population,
        code_departement = EXCLUDED.code_departement,
        code_region = EXCLUDED.code_region,
        fetched_at = EXCLUDED.fetched_at
"""

def enrich_communes(batch_size: int = 5000) -> tuple[int, int]:
    """Fetch geo data for every commune in gold that we don't already have. Returns (ok, failed)."""
    ok = failed = 0

    with psycopg.connect(CONN_STR) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT g.code_commune
                FROM gold_commune_yearly_stats g
                LEFT JOIN commune_reference r ON r.code_commune = g.code_commune
                WHERE r.code_commune IS NULL
            """)
            missing_codes = [row[0] for row in cur.fetchall()]

        if not missing_codes:
            log.info("all communes are already enriched")
            return 0, 0

        log.info("fetching geo data for %d communes not yet enriched", len(missing_codes))

        rows_to_insert = []
        now = datetime.now(timezone.utc)

        # For larger sets, fetch national reference dataset in bulk (1-2 API calls instead of thousands)
        if len(missing_codes) > 20:
            log.info("fetching national communes dataset in bulk from geo API...")
            all_communes = fetch_all_communes()
            commune_lookup = {c["code"]: c for c in all_communes if "code" in c}
            log.info("fetched %d reference communes", len(commune_lookup))

            remaining_codes = []
            for code in missing_codes:
                if code in commune_lookup:
                    data = commune_lookup[code]
                    departement = (data.get("departement") or {}).get("code")
                    region = (data.get("region") or {}).get("code")
                    rows_to_insert.append((
                        code,
                        data.get("nom"),
                        data.get("population"),
                        departement,
                        region,
                        now,
                    ))
                    ok += 1
                else:
                    remaining_codes.append(code)
        else:
            remaining_codes = missing_codes

        # Fallback for codes not found in bulk reference (or when only a few codes are missing)
        if remaining_codes:
            log.info("fetching remaining %d communes individually", len(remaining_codes))
            for code in remaining_codes:
                try:
                    data = fetch_commune(code)
                    departement = (data.get("departement") or {}).get("code")
                    region = (data.get("region") or {}).get("code")
                    rows_to_insert.append((
                        code,
                        data.get("nom"),
                        data.get("population"),
                        departement,
                        region,
                        now,
                    ))
                    ok += 1
                except GeoApiError as e:
                    failed += 1
                    log.warning("could not enrich commune %s: %s", code, e)

        # Batch upsert into database in chunks
        if rows_to_insert:
            log.info("persisting %d commune records to database...", len(rows_to_insert))
            with conn.cursor() as cur:
                for i in range(0, len(rows_to_insert), batch_size):
                    chunk = rows_to_insert[i : i + batch_size]
                    cur.executemany(UPSERT_SQL, chunk)
            conn.commit()

    log.info("enrichment done: %d ok, %d failed", ok, failed)
    return ok, failed