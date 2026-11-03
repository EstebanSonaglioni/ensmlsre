# MLSRE

## Demo en HackerRank

```bash
./scripts/up-local.sh
```

Abrí el Preview de **:3000**. Login: **`boss@mail.com`** / **`mlsre-demo`** (admin de tienda: dashboard, ventas, preguntas).

Misma clave **`mlsre-demo`** para: `ventas1@mail.com`, `ventas2@mail.com` (vendedores) y `compras1@mail.com`, `compras2@mail.com` (compradores).

Eshop con panel de vendedor: catálogo, compras, preguntas, chat de órdenes y métricas.

- App: http://localhost:3000 (secundario: **3100**)
- API: http://localhost:8000 (secundario: **8010**)
- Grafana (logs): http://localhost:3001 (secundario: **3011**)

## Repositorio

Código en GitHub: [EstebanSonaglioni/ensmlsre](https://github.com/EstebanSonaglioni/ensmlsre).

```bash
git clone https://github.com/EstebanSonaglioni/ensmlsre.git
cd ensmlsre
```

SSH: `git clone git@github.com:EstebanSonaglioni/ensmlsre.git`. ZIP: [Code → Download ZIP](https://github.com/EstebanSonaglioni/ensmlsre/archive/refs/heads/main.zip).

## Documentación

| Dónde | Qué |
| --- | --- |
| Este `README.md` | Arranque local (Compose y sin Docker) |
| [`docs/adr/`](docs/adr/README.md) | Decisiones de arquitectura (ADR 0001–0016) |
| [`docs/plans/`](docs/plans/) | Planes de features |
| [`AGENTS.md`](AGENTS.md) | Stack y reglas de implementación |
| [`STYLE.md`](STYLE.md) | Guía visual del dashboard |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de cambios |

## Requisitos

**Con Docker** (camino completo, incluye Grafana):

- [Docker Engine](https://docs.docker.com/engine/install/) y [Docker Compose](https://docs.docker.com/compose/install/) (plugin v2)
- Puertos libres (default → secundario si está ocupado): **3000 / 3100** (frontend), **8000 / 8010** (API), **3001 / 3011** (Grafana), **5433 / 5434** (Postgres en el host)

**Sin Docker** (HackerRank / host): Python 3.12, red a PyPI (`get-pip`), Node 22 para la UI. SQLite (stdlib). No hace falta Postgres. Observabilidad Grafana/Loki **no** entra en este modo.

## Sin Docker (host / HackerRank)

```bash
./scripts/up-local.sh
# o solo API si no hay Node reciente:
./scripts/up-local.sh --api-only
```

Usa SQLite en `backend/var/mlsre.db` (no pisa el `.env` de Compose). Crea `backend/.venv` con `--without-pip` y get-pip (PEP 668). Schema con `create_all`, después el seed demo (`boss@mail.com` / `mlsre-demo`). UI en `:3000`; el browser llama `/backend` (Next lo reescribe a uvicorn en `:8000`). En HackerRank el Preview es esa UI. `npm start` en `frontend` es `next dev` en `0.0.0.0:3000`. Detalle: `docs/plans/arranque-local-sin-docker.md`, ADR 0015 y 0016.

Si tenés Postgres en el host: `USE_POSTGRES=1 ./scripts/up-local.sh` y un `.env` con `DATABASE_URL` postgresql.

## Despliegue local con Docker (después de clonar)

1. Cloná el repositorio (ver [Repositorio](#repositorio)) y entrá a la carpeta.

2. Generá `.env` y levantá el stack. Lo más directo:

   ```bash
   ./scripts/up.sh
   ```

   El script:

   - Crea `.env` si no existe. No lo subas al repo. No imprime contraseñas.
   - Pone valores **aleatorios** en: `POSTGRES_PASSWORD`, `APP_DB_PASSWORD`, `MIGRATION_DB_PASSWORD`, `JWT_SECRET`, `GRAFANA_ADMIN_PASSWORD`. Arma `DATABASE_URL` y `MIGRATION_DATABASE_URL` con esas claves (host `db`, puerto `5432` en la red de Compose).
   - Usa **defaults** en el resto (igual que `.env.example`): `POSTGRES_DB=mlsre`, `APP_DB_USER=mlsre_app`, `MIGRATION_DB_USER=mlsre_migrate`, `GRAFANA_ADMIN_USER=admin`, directorios de imágenes y logs, puertos 3000 / 8000 / 3001 / 5433.
   - Si un puerto default está ocupado, pasa al secundario (3100 / 8010 / 3011 / 5434) y alinea `CORS_ORIGINS` y `NEXT_PUBLIC_API_URL`.
   - Corre `docker compose up --build`.

   Opciones:

   ```bash
   ./scripts/up.sh --detach     # segundo plano (-d)
   ./scripts/up.sh --fresh-env  # reescribe .env con secretos nuevos
   ./scripts/up.sh --help
   ```

   Si ya hay `.env`, lo reusa (salvo `--fresh-env`). `--fresh-env` con un volumen de Postgres viejo deja claves que no coinciden; en ese caso: `docker compose down -v` y volvé a levantar.

   Grafana: usuario `admin`, contraseña la de `GRAFANA_ADMIN_PASSWORD` en `.env`.

   Alternativa manual: copiá el example y completá los placeholders:

   ```bash
   cp .env.example .env
   ```

   En un `.env` armado a mano tenés que definir al menos:

   - `POSTGRES_PASSWORD`, `APP_DB_PASSWORD`, `MIGRATION_DB_PASSWORD`
   - `DATABASE_URL` y `MIGRATION_DATABASE_URL` (mismos usuarios/claves que arriba; host **`db`**, puerto **5432** dentro de la red de Compose)
   - `JWT_SECRET` (mínimo 32 caracteres aleatorios; el backend rechaza `change-me`)
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

3. Si armaste `.env` a mano, levantá todo (build + migraciones + servicios):

   ```bash
   docker compose up --build
   ```

   Con `./scripts/up.sh` este paso ya corrió. La primera vez tarda: construye backend y frontend, crea Postgres (roles de app y migraciones), corre `alembic upgrade head` y el seed demo.

4. Cuando el backend esté healthy y el frontend escuchando:

   | Servicio | URL (default) | URL (secundario) |
   | --- | --- | --- |
   | Tienda (Next.js) | http://localhost:3000 | http://localhost:3100 |
   | API (FastAPI) | http://localhost:8000 | http://localhost:8010 |
   | Health | http://localhost:8000/health | http://localhost:8010/health |
   | Grafana | http://localhost:3001 | http://localhost:3011 |

5. Al levantar, el servicio `seed` carga una demo (si `boss@mail.com` todavía no existe). Contraseña de todos: `DEMO_PASSWORD` (default **`mlsre-demo`**).

   | Email | Rol |
   | --- | --- |
   | `boss@mail.com` | Admin de la tienda Almacén MLSRE |
   | `ventas1@mail.com` / `ventas2@mail.com` | Vendedores (productos repartidos) |
   | `compras1@mail.com` / `compras2@mail.com` | Compradores |

   Hay publicaciones (fotos en `backend/seed/products`, nombre = archivo sin extensión), ventas/compras, preguntas y respuestas, y órdenes abiertas. Las ventas completadas se esparcen en **90 días** para los gráficos 7/30/90. Si el seed ya corrió, no duplica. Volumen de Postgres nuevo: `docker compose down -v` y volvé a levantar.

6. También podés crear otra cuenta desde la tienda. El primer usuario nuevo es comprador; desde el perfil crea tienda o acepta invitación.

7. Logs: el backend escribe JSON en `backend/var/logs/app.log` (no se versiona). Alloy lo envía a Loki. En Grafana → Explore → datasource **Loki** → `{job="backend"}`. El dashboard **API SLI / SLO / SLA** (carpeta MLSRE) muestra disponibilidad, latencia, error budget y umbrales SLO/SLA. Detalle en `docs/sli-slo-sla.md`.

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

O en el host, apuntando a Postgres en `127.0.0.1:${POSTGRES_HOST_PORT}` (default **5433**, secundario **5434**; publicado solo en loopback). Los tests leen esa variable del `.env`.

## Stack

Backend FastAPI + Postgres 16 + Alembic (Compose) o SQLite en host. Frontend Next.js (App Router). Arranque Compose: `compose.yaml`. Arranque host: `./scripts/up-local.sh`.
