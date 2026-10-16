# DVF ELT Pipeline

A batch ELT pipeline that ingests French public real-estate transaction data (DVF —
Demandes de Valeurs Foncières) and produces clean, query-ready price statistics per
commune and year.

Built as a portfolio project to practice real data engineering patterns: idempotent
loads, data quality checks, a layered (bronze/silver/gold) warehouse, and pipeline
orchestration with failure tracking.

## What it does

1. **Ingest** — downloads the yearly DVF file from data.gouv.fr, streamed and
   checksummed, with every download recorded in a manifest.
2. **Bronze** — loads the raw CSV into Postgres, exactly as received.
3. **Silver** — deduplicates, filters out invalid rows (zero price, missing date),
   and computes price per square meter.
4. **Gold** — aggregates silver into per-commune, per-year statistics: transaction
   count, average/median/min/max price per m².
5. **Enrichment** — commune population and administrative data from the French
   government geo API, joined against gold for richer analysis (e.g. average
   price by commune size).

Every stage is idempotent: re-running the pipeline on the same source file never
duplicates data. Every pipeline run is recorded in `pipeline_executions`, with
per-stage status, so a failure at any step is traceable after the fact.

## Architecture

[paste the diagram from Step 2 here]

## Tech stack

- Python 3.11 (ingestion, orchestration, data access)
- PostgreSQL 16, running in Docker
- pytest (unit tests with mocked HTTP, integration tests against a real database)
- GitHub Actions (CI: lint + unit tests on every push/PR)
- AWS S3 (data lake storage), IAM (least-privilege access)
- Snowflake (cloud data warehouse)

## How to run it

Prerequisites: Docker, Python 3.11+.

```bash
git clone <your-repo-url>
cd dvf-elt
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
docker compose -f docker/docker-compose.yml up -d
docker exec -i dvf_postgres psql -U dvf_user -d dvf < sql/bronze_dvf.sql
docker exec -i dvf_postgres psql -U dvf_user -d dvf < sql/silver_dvf.sql
docker exec -i dvf_postgres psql -U dvf_user -d dvf < sql/gold_dvf.sql
docker exec -i dvf_postgres psql -U dvf_user -d dvf < sql/pipeline_runs.sql
docker exec -i dvf_postgres psql -U dvf_user -d dvf < sql/pipeline_executions.sql
docker exec -i dvf_postgres psql -U dvf_user -d dvf < sql/commune_reference.sql
python -m dvf_elt.run_pipeline_cli
```

## Running the tests

```bash
pytest -v -m "not integration"   # fast, no database needed
pytest -v -m integration          # needs the Postgres container running
```

## What I verified, not just assumed

- Running the pipeline twice on the same file does not duplicate rows (proven in
  `tests/test_load_bronze.py` and `tests/test_gold.py`, and manually via Day 7/9
  checklists).
- A missing source file fails cleanly at the bronze stage without touching silver
  or gold (`pipeline_executions` records this).
- A crash mid-pipeline (simulated at the silver stage) is recorded accurately —
  bronze shows success, silver shows failed, gold is never attempted.
- Gold totals reconcile exactly against silver row counts (`tests/test_gold.py`).
- Geo API enrichment (commune population, département, région) is fetched,
  cached, and automatically wired into the orchestrated pipeline as a fourth
  stage, with its own failure tracking.
- AWS access is scoped to least-privilege: the pipeline's IAM user can only
  read/write objects in its own S3 bucket, nothing else in the account.
- CI runs the full test suite — including integration tests against a real,
  disposable Postgres database — on every push and pull request, not just
  unit tests.

## Known limitations (being worked on)

- Single-machine, single-file pipeline — no incremental/multi-year loading yet.
- Geo API client (commune enrichment) is built and tested but not yet wired into
  the main pipeline.
- No cloud storage or warehouse yet — Postgres is local. S3 + Snowflake planned next.
- No scheduler yet — the pipeline is run manually. Airflow planned.
- Snowflake loading (S3 -> Snowflake) is done via manual SQL, not yet part of
  the orchestrated pipeline.
- No dbt yet — Snowflake transformations are plain SQL for now.

## Project structure

```
dvf-elt/
├── src/dvf_elt/
│   ├── ingest/        # download, parsing, geo API client
│   ├── load/           # bronze/silver/gold loaders
│   ├── quality/        # automated data quality checks
│   └── pipeline.py     # orchestrates bronze -> silver -> gold
├── sql/                # DDL + transformation SQL
├── tests/               # unit tests (mocked) + integration tests (real DB)
├── docker/              # Postgres via docker-compose
└── .github/workflows/  # CI: lint + test on every push
```