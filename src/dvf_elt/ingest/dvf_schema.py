from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class DvfTransaction:
    date_mutation: date
    valeur_fonciere: float
    code_commune: str
    nom_commune: str
    type_local: str | None
    surface_reelle_bati: float | None

class DvfRowError(Exception):
    """Raised when a raw CSV row cannot be turned into a DvfTransaction."""