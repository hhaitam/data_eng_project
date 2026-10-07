# ADR 0001: Use local Postgres before moving to Snowflake

## Status
Accepted

## Context
The pipeline needs a warehouse to hold bronze/silver/gold layers. The eventual
target is Snowflake, matching the primary tech stack and target job market.

## Decision
Build and prove the bronze -> silver -> gold logic against a local Postgres
instance (via Docker) first, before introducing Snowflake.

## Why
- Postgres is free, fast to iterate against, and requires no cloud account or
  trial-period clock to start.
- The SQL patterns (idempotent delete-then-insert, deduplication, aggregation)
  are close enough to standard SQL that moving them to Snowflake later is a
  port, not a rewrite.
- It forces understanding of the underlying logic (transactions, idempotency,
  constraints) rather than leaning on a cloud platform's managed features
  before those fundamentals are solid.

## Consequences
- Some Snowflake-specific concepts (warehouses, micro-partitions, clustering,
  RBAC, resource monitors) are not exercised by this stage and are deferred to
  the Snowflake migration step.
- The migration step itself becomes a demonstrable piece of the project: moving
  a working pipeline from one warehouse to another is a real, intentional
  decision, not a starting assumption.