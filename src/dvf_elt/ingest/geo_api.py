import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://geo.api.gouv.fr"

class GeoApiError(Exception):
    pass

def fetch_commune(code_commune: str, max_retries: int = 3, backoff_base: float = 1.5) -> dict[str, Any]:
    """Fetch commune metadata (name, population, coords) with retry on transient errors."""
    url = f"{BASE_URL}/communes/{code_commune}"
    params = {"fields": "nom,code,population,centre,departement,region"}

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=10)
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