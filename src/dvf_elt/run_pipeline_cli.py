import logging
from datetime import date
from pathlib import Path

from dvf_elt.logging_conf import setup_logging
from dvf_elt.pipeline import run_pipeline, PipelineError

def main():
    setup_logging()
    csv_path = Path("data/raw/dvf_2025.csv.gz")
    quarantine_path = Path("data/quarantine/dvf_2025.log")
    as_of_date = date(2025, 1, 1)

    try:
        run_pipeline(csv_path, quarantine_path, as_of_date)
    except PipelineError as e:
        logging.error("Pipeline failed: %s", e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()