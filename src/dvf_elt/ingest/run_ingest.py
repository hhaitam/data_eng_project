import logging
from pathlib import Path

from dvf_elt.config import DVF_URL, DVF_YEAR, DATA_RAW
from dvf_elt.ingest.download import download_file
from dvf_elt.ingest.manifest import load_manifest, record
from dvf_elt.logging_conf import setup_logging

log = logging.getLogger(__name__)

def main():
    setup_logging()
    manifest = load_manifest()
    key = f"dvf_{DVF_YEAR}"
    dest = DATA_RAW / f"{key}.csv.gz"

    sha = download_file(DVF_URL, dest)
    size = dest.stat().st_size
    record(manifest, key, sha, DVF_URL, size)
    log.info("manifest updated for %s (%d bytes)", key, size)

if __name__ == "__main__":
    main()