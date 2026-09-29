import hashlib, logging
from pathlib import Path
import requests

log = logging.getLogger(__name__)

def download_file(url: str, dest: Path, timeout: int = 30) -> str:
    """Stream url to dest atomically; return the sha256 hex digest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    sha = hashlib.sha256()
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                sha.update(chunk)
    tmp.replace(dest)
    log.info("downloaded %s -> %s sha256=%s", url, dest, sha.hexdigest()[:12])
    return sha.hexdigest()