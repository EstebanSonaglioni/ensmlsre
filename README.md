# MLSRE

Eshop con panel de vendedor: catálogo, compras, preguntas, chat de órdenes y métricas.

- App: http://localhost:3000 (secundario: **3100**)
- API: http://localhost:8000 (secundario: **8010**)
- Grafana (logs): http://localhost:3001 (secundario: **3011**)

## Requisitos

En la PC donde vas a levantar el proyecto:

- [Docker Engine](https://docs.docker.com/engine/install/) y [Docker Compose](https://docs.docker.com/compose/install/) (plugin v2)
- Puertos libres (default → secundario si está ocupado): **3000 / 3100** (frontend), **8000 / 8010** (API), **3001 / 3011** (Grafana), **5433 / 5434** (Postgres en el host)

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
   - `CORS_ORIGINS=http://localhost:3000` (si cambiaste `FRONTEND_PORT`, usá ese puerto)
   - `NEXT_PUBLIC_API_URL=http://localhost:8000` (si cambiaste `BACKEND_PORT`, usá ese puerto)
   - `GRAFANA_ADMIN_USER` y `GRAFANA_ADMIN_PASSWORD`
   - Puertos en el host (opcional; default entre paréntesis): `FRONTEND_PORT` (3000), `BACKEND_PORT` (8000), `GRAFANA_PORT` (3001), `POSTGRES_HOST_PORT` (5433)

   No subas `.env` al repo.

   Si Compose falla con `port is already allocated` o `address already in use`, el puerto del host está ocupado. En `.env` pasá a los secundarios y alineá CORS/API:

   ```bash
   FRONTEND_PORT=3100
   BACKEND_PORT=8010
   GRAFANA_PORT=3011
   POSTGRES_HOST_PORT=5434
   CORS_ORIGINS=http://localhost:3100
   NEXT_PUBLIC_API_URL=http://localhost:8010
   ```

   Podés cambiar solo el que chocó. Después: `docker compose up --build`. Dentro de la red de Compose los contenedores siguen en 3000, 8000 y 5432; solo cambia lo que publica el host.

3. Levantá todo (build + migraciones + servicios):

   ```bash
   docker compose up --build
   ```

   La primera vez tarda: construye backend y frontend, crea Postgres (roles de app y migraciones) y corre `alembic upgrade head`.

4. Cuando el backend esté healthy y el frontend escuchando:

   | Servicio | URL (default) | URL (secundario) |
   | --- | --- | --- |
   | Tienda (Next.js) | http://localhost:3000 | http://localhost:3100 |
   | API (FastAPI) | http://localhost:8000 | http://localhost:8010 |
   | Health | http://localhost:8000/health | http://localhost:8010/health |
   | Grafana | http://localhost:3001 | http://localhost:3011 |

5. Entrá a la URL de la tienda y **creá una cuenta**. El primer usuario es comprador. Desde el perfil puede crear una tienda (pasa a vendedor) o aceptar una invitación.

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

O en el host, apuntando a Postgres en `localhost:${POSTGRES_HOST_PORT}` (default **5433**, secundario **5434**; los tests leen esa variable del `.env`).

## Stack

Backend FastAPI + Postgres 16 + Alembic. Frontend Next.js (App Router). Arranque único: `compose.yaml` en la raíz.
