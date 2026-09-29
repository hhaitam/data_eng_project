import csv
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator

from dvf_elt.ingest.dvf_schema import DvfTransaction, DvfRowError

log = logging.getLogger(__name__)

def _parse_row(row: dict) -> DvfTransaction:
    try:
        return DvfTransaction(
            date_mutation=datetime.strptime(row["date_mutation"], "%Y-%m-%d").date(),
            valeur_fonciere=float(row["valeur_fonciere"]) if row["valeur_fonciere"] else 0.0,
            code_commune=row["code_commune"],
            nom_commune=row["nom_commune"],
            type_local=row["type_local"] or None,
            surface_reelle_bati=float(row["surface_reelle_bati"]) if row.get("surface_reelle_bati") else None,
        )
    except (KeyError, ValueError) as e:
        raise DvfRowError(f"{e}: {row}") from e

def parse_dvf_file(path: Path, quarantine_path: Path) -> Iterator[DvfTransaction]:
    total = ok = bad = 0
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "rt", encoding="utf-8") as f, \
         quarantine_path.open("w", encoding="utf-8") as qf:
        reader = csv.DictReader(f, delimiter="|")  # adjust delimiter to what you saw in Step 1
        for row in reader:
            total += 1
            try:
                yield _parse_row(row)
                ok += 1
            except DvfRowError as e:
                bad += 1
                qf.write(str(e) + "\n")
    log.info("parsed %s: total=%d ok=%d bad=%d (%.2f%% bad)", path.name, total, ok, bad, 100 * bad / max(total, 1))