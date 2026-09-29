import json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_PATH = Path("data/raw/manifest.json")

def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}

def record(manifest: dict, key: str, sha256: str, url: str, size_bytes: int) -> dict:
    manifest[key] = {
        "url": url,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    return manifest