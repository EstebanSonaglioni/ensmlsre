# Arranque local sin Docker (Compose se queda)

HackerRank no tiene Docker ni pip de sistema; puede no tener Postgres. Grafana/Loki/Alloy quedan solo en Compose.

## Confirmado en HR

Python 3.12.3 linux, sin `pip` ni `ensurepip`. `get-pip --user` choca PEP 668.

Camino que funciona:

```bash
python3 -m venv --without-pip backend/.venv
curl -sS https://bootstrap.pypa.io/get-pip.py | backend/.venv/bin/python3
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

Argon2 instala por wheel manylinux. SQLite vía stdlib.

## App

- `DATABASE_URL` sqlite: mismo archivo que migraciones; `create_all` (Alembic de Postgres no se reescribe).
- `date_trunc` portable en el dashboard.
- `./scripts/up-local.sh`: venv, get-pip, schema, seed, uvicorn + `npm start`.
- Browser → `/backend` → Next rewrite → uvicorn (`127.0.0.1:8000`). Preview HR solo usa `:3000`.
- `allowedDevOrigins` y CSP/CORS para el host proxy de HR. Cookie `Path=/backend/auth`.
- Compose no se modifica.
