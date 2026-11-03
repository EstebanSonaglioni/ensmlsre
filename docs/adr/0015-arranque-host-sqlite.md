# ADR 0015: Arranque en host con SQLite

- Status: aceptada
- Date: 2026-11-02

## Context

HackerRank no ofrece Docker ni pip de sistema (PEP 668). Puede no haber Postgres. Hay que poder correr API + UI sin reescribir Compose.

## Decision

- `docker compose up --build` sigue siendo el camino con Postgres, dos roles y Grafana.
- `./scripts/up-local.sh` usa SQLite (`backend/var/mlsre.db`), `create_all` desde modelos, seed demo. Alembic no se corre en SQLite.
- venv `--without-pip` + get-pip al intérprete del venv (confirmado en HR + argon2 wheel).
- `date_trunc` del dashboard se traduce a `strftime` en SQLite.
- Grafana/Alloy/Loki no se levantan en este modo.

## Consequences

SQLite no replica índices parciales ni roles DML/DDL. Tests de Compose siguen contra Postgres. Hay que commitear `backend/seed/` y `app/seed.py` para que un clone tenga fotos demo.
