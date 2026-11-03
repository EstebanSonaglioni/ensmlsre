# ADR 0001: Stack y arranque local con Compose

- Status: aceptada
- Date: 2026-11-01

## Contexto

El equipo necesita un único camino para clonar y levantar el eshop (API, UI, Postgres, logs) sin instalar Python/Node en el host, con versiones fijas.

## Decision

- Backend: Python 3.12, FastAPI, Uvicorn, SQLAlchemy, Alembic, Ruff, Pytest.
- Frontend: TypeScript, Next.js App Router, Tailwind + shadcn según `STYLE.md`, axios.
- Datos: Postgres 16. Un `compose.yaml` en la raíz; `docker compose up --build` es el arranque.
- Código en `/backend` y `/frontend`. Un `CHANGELOG.md` en la raíz.
- Puertos de host configurables (`FRONTEND_PORT`, `BACKEND_PORT`, `GRAFANA_PORT`, `POSTGRES_HOST_PORT`) con secundarios si el default está ocupado. Entre contenedores se usan los nombres `db` y `backend`. El browser usa `localhost`.

## Consecuencias

No hay “modo host” de primera clase. Las variables que lee el browser (`NEXT_PUBLIC_API_URL`, CORS) no usan el DNS interno de Compose. El detalle de servicios está en `AGENTS.md` y el README.
