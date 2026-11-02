# MLSRE

Eshop con panel de vendedor: catálogo, compras, preguntas, chat de órdenes y métricas.

- App: http://localhost:3000
- API: http://localhost:8000
- Grafana (logs): http://localhost:3001

## Requisitos

En la PC donde vas a levantar el proyecto:

- [Docker Engine](https://docs.docker.com/engine/install/) y [Docker Compose](https://docs.docker.com/compose/install/) (plugin v2)
- Puertos libres: **3000** (frontend), **8000** (API), **3001** (Grafana), **5433** (Postgres en el host)

No hace falta instalar Python ni Node en el host: todo corre en Compose.

## Despliegue local (después de clonar)

1. Cloná el repositorio y entrá a la carpeta:

   ```bash
   git clone <url-del-repo>
   cd MLSRE
   ```

2. Copiá las variables de entorno y cambiá los placeholders (`change-me` y secretos):

   ```bash
   cp .env.example .env
   ```

   En `.env` tenés que definir al menos:

   - `POSTGRES_PASSWORD`, `APP_DB_PASSWORD`, `MIGRATION_DB_PASSWORD`
   - `DATABASE_URL` y `MIGRATION_DATABASE_URL` (mismos usuarios/claves que arriba; host **`db`**, puerto **5432** dentro de la red de Compose)
   - `JWT_SECRET` (largo y aleatorio; no uses el valor de ejemplo)
   - `CORS_ORIGINS=http://localhost:3000`
   - `NEXT_PUBLIC_API_URL=http://localhost:8000`
   - `GRAFANA_ADMIN_USER` y `GRAFANA_ADMIN_PASSWORD`

   No subas `.env` al repo.

3. Levantá todo (build + migraciones + servicios):

   ```bash
   docker compose up --build
   ```

   La primera vez tarda: construye backend y frontend, crea Postgres (roles de app y migraciones) y corre `alembic upgrade head`.

4. Cuando el backend esté healthy y el frontend escuchando:

   | Servicio | URL |
   | --- | --- |
   | Tienda (Next.js) | http://localhost:3000 |
   | API (FastAPI) | http://localhost:8000 |
   | Health | http://localhost:8000/health |
   | Grafana | http://localhost:3001 |

5. Entrá a http://localhost:3000 y **creá una cuenta**. El primer usuario es comprador. Desde el perfil puede crear una tienda (pasa a vendedor) o aceptar una invitación.

6. Logs: el backend escribe JSON en `backend/var/logs/app.log` (no se versiona). Alloy lo envía a Loki. En Grafana → Explore → datasource **Loki** → `{job="backend"}`.

Para parar:

```bash
docker compose down
```

Los datos de Postgres, Loki y Grafana quedan en volúmenes de Compose. Para borrar también los datos:

```bash
docker compose down -v
```

## Tests del backend

Con el servicio `db` arriba (Compose):

```bash
docker compose exec backend pytest
```

O en el host, apuntando a Postgres en `localhost:5433` (ver `DATABASE_URL` adaptada en los tests).

## Stack

Backend FastAPI + Postgres 16 + Alembic. Frontend Next.js (App Router). Arranque único: `compose.yaml` en la raíz.
