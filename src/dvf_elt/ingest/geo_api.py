import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://geo.api.gouv.fr"

class GeoApiError(Exception):
    pass

def fetch_commune(
    code_commune: str,
    max_retries: int = 3,
    backoff_base: float = 1.5,
    session: requests.Session | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    """Fetch commune metadata (name, population, coords) with retry on transient errors."""
    url = f"{BASE_URL}/communes/{code_commune}"
    params = {"fields": "nom,code,population,centre,departement,region"}
    http = session or requests

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = http.get(url, params=params, timeout=timeout)
            if resp.status_code == 404:
                raise GeoApiError(f"commune {code_commune} not found")
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            wait = backoff_base ** attempt
            log.warning("geo api attempt %d/%d failed for %s: %s (retrying in %.1fs)",
                        attempt, max_retries, code_commune, e, wait)
            time.sleep(wait)
    raise GeoApiError(f"failed after {max_retries} attempts for {code_commune}") from last_exc


def fetch_all_communes(
    include_arrondissements: bool = True,
    max_retries: int = 3,
    backoff_base: float = 1.5,
    timeout: int = 30,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Fetch all French communes (and arrondissements) in bulk via geo.api.gouv.fr."""
    http = session or requests
    endpoints = [
        (f"{BASE_URL}/communes", {"fields": "nom,code,population,departement,region"}),
    ]
    if include_arrondissements:
        endpoints.append(
            (f"{BASE_URL}/communes", {"type": "arrondissement-municipal", "fields": "nom,code,population,departement,region"})
        )

    all_data: list[dict[str, Any]] = []
    for url, params in endpoints:
        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = http.get(url, params=params, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    all_data.extend(data)
                break
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exc = e
                wait = backoff_base ** attempt
                log.warning("geo api bulk attempt %d/%d failed for %s: %s (retrying in %.1fs)",
                            attempt, max_retries, url, e, wait)
                time.sleep(wait)
        else:
            raise GeoApiError(f"bulk fetch failed after {max_retries} attempts for {url}") from last_exc

    return all_data