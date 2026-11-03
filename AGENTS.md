# STACK TECNOLOGICO: 

## Backend:
  - Lenguaje: Python
  - Framework: FastAPI + Uvicorn
  - DB: Postgresql
  - ORM: SqlAlchemy
  - Auth: JWT (HS256, secreto en variable de entorno)
  - Linter: ruff
  - Migraciones: alembic
  - Tests: pytest

## Frontend: 
  - Lenguaje: Typescript
  - Framework: NextJS (App Router)
  - Estilos: Tailwind CSS y shadcn/ui, siguiendo `STYLE.md`
  - Requests: axios
  - Linter: eslint
  - Tests: vitest + Testing Library
  - Pantallas de carga: `loading.tsx`

## Infra:
  - Arranque local: Docker + Docker Compose

# Reglas generales para agentes:
  - Cambios atomicos, centrados en las features a desarrollar.
  - No commitear datos sensibles.
  - Cada cambio de feature queda registrado en un único CHANGELOG.md en la raíz del repo, una entrada por cambio.
  - Todo el backend está en /backend
  - Todo el frontend está en /frontend
  - Este archivo fija reglas de implementación. No describe el dominio funcional del proyecto.
  
# Generales:
   - No versionar .env, e incluir .env.example
   - Por cada funcionalidad desarrollada debe haber al menos un test del happy path y tests de casos de esquina. Backend con pytest: autenticación, autorización, validación de entradas, CORS y regresiones de seguridad. Frontend con vitest: happy path y casos de esquina de UI (login, listados, mensajes de `detail`).
   - Errores al cliente: código HTTP apropiado y body `{ "detail": "<mensaje general>" }`. El mensaje va en español, sin stack ni datos internos.
   - /backend y /frontend: dependencias con versiones bloqueadas (lockfiles) y análisis de vulnerabilidades en CI con pip-audit y npm audit.

## Backend: 
   - Access token JWT: expiración de 15 minutos, algoritmo HS256, incluye el rol. El cliente lo guarda solo en memoria y lo envía en el header Authorization en cada petición que lo requiera. No se persiste en localStorage. JavaScript no escribe cookies de sesión.
   - Refresh token: expiración de 7 días. Cookie HttpOnly, Secure, SameSite=None (el browser en :3000 y la API en :8000 son orígenes distintos; Lax no envía la cookie). Path acotado a `/auth`. JavaScript no la lee. La setea el backend en registro e inicio de sesión. Al recargar, `GET /auth/me` la usa para devolver de nuevo el access token.
   - Al recargar la página el access token se pierde y se restaura con la cookie HttpOnly.
   - CSRF solo en los endpoints que se autentican con la cookie de refresh (refresh y logout/revocación). El resto de la API usa el header Authorization y no mezcla esa cookie con el access token.
   - El hash de contraseñas se hace con argon2id, con los parámetros por defecto de la librería. No se devuelve nunca ningún hash.
   - CORS: permitir únicamente orígenes, métodos y headers necesarios.
   - Abuso y disponibilidad: login limitado a 5 intentos por minuto por IP; rate limiting también en el resto de endpoints sensibles. Body máximo 1 MB. Timeout de request 30 s. Paginación con máximo 100 ítems por página.
   - Dos roles de Postgres: el de la aplicación solo DML (sin DDL); Alembic corre con un rol distinto que sí puede hacer DDL.
   - Observabilidad: propagar request_id. Log estructurado de cada request. Los fallos de autenticación y los errores repetidos se registran en ese log. No hay sistema externo de alertas. La retención de logs es una regla de operación: no commitear logs y no incluir secretos.
   - Se validan los inputs con Pydantic
   - Layout: routers/, schemas/, models/, services/, core/(config, security)
   - Logging de las llamadas a los endpoints con structlog, no se utiliza print.
   - El log debe tener: request_id, method, path, status, latency, user_id (si corresponde)
   - No se loggean passwords, tokens, cookies, ni otros datos sensibles
   - Loggear errores (nivel ERROR) inesperados con stack, solo en el servidor.
   - Ante una exception, loggear con stack y no devolver stacktrace al frontend. La respuesta sigue el body `{ "detail": "<mensaje general>" }`.
   - Prevencion de SQLInjection: no construir llamadas sql con f-strings, .format o concat de inputs del usuario. Las construcciones de instrucciones sql se forman preferentemente con el ORM, si se necesita SQL puro usar bound parameters solamente. Validar ids y enums con pydantic antes de escribir en la db.


## Frontend:
  - Los estilos siguen `STYLE.md` (dashboard seller dark: tokens, tipografía, layout, componentes). Tailwind CSS y shadcn/ui implementan esa guía; no inventar otra paleta.
  - Se llama a la api a través del cliente en NEXT_PUBLIC_API_URL
  - El access token vive solo en memoria y se manda en Authorization. La cookie HttpOnly de sesión la setea el backend; el cliente no la lee ni la guarda en localStorage. Al cargar la app se llama a `GET /auth/me` con `withCredentials: true` para restaurar la sesión.
  - Las pantallas de carga se muestran con `loading.tsx`
  - No se muestran errores detallados al cliente, solo el mensaje general del campo `detail`. Los logs detallados quedan en el backend.
  - Prevención de XSS: renderizar texto por defecto. Evitar "dangerouslySetInnerHtml" a menos que esté saneado. Header `x-content-type-options: nosniff`. Cuando exista el frontend, Content-Security-Policy con nonce en el middleware. No inventar una policy que rompa Next antes de que el frontend exista.
  - No guardar datos sensibles en localStorage.
  - Las llamadas que dependen de la cookie de sesión (`/auth/register`, `/auth/login`, `/auth/me`) usan axios con `withCredentials: true`. El resto de las llamadas manda el access token en Authorization.

# Docker y Compose:
  El proyecto se levanta desde la raíz con `docker compose up --build`. Esa es la forma de correrlo en local.

  Archivos:
  - `compose.yaml` en la raíz. Un solo archivo, para desarrollo local.
  - `backend/Dockerfile` y `backend/.dockerignore`
  - `frontend/Dockerfile` y `frontend/.dockerignore`
  - `docker/postgres/init/` con el script que crea los dos roles de Postgres. Se monta en `/docker-entrypoint-initdb.d` y solo corre cuando el volumen de datos está vacío.

  Imágenes base:
  - Backend: `python:3.12-slim`
  - Frontend: `node:22-alpine`
  - Base de datos: `postgres:16-alpine`
  - Backend y frontend corren con usuario no root.

  Servicios de `compose.yaml`:
  - `db`: Postgres 16, volumen nombrado `postgres_data`, healthcheck con `pg_isready`. Publica `5433` en el host (`5432` en el contenedor) para no chocar con otro Postgres local. El superusuario de la imagen solo inicializa el cluster; la app no se conecta con ese rol.
  - `migrate`: one-shot, `alembic upgrade head` con el rol de migraciones (DDL). `restart: "no"`. Termina con éxito antes de que arranque el backend (`service_completed_successfully`).
  - `backend`: build `./backend`, publica `8000`, escucha en `0.0.0.0:8000` con uvicorn `--reload`. Bind mount del código (incluye `var/product-images`) y volumen aparte para el virtualenv del contenedor. Depende de `db` saludable y de `migrate` completado. Healthcheck HTTP a `GET /health`, sin autenticación.
  - `frontend`: build `./frontend`, publica `3000`, `next dev` en `0.0.0.0:3000`. Bind mount del código y volumen aparte para `node_modules`. Depende del backend.

  Red y URLs:
  - Una red bridge de Compose. Entre contenedores se usan los nombres `db` y `backend`.
  - El browser corre en el host. `NEXT_PUBLIC_API_URL` es `http://localhost:8000`. Las variables que lee el browser no usan el nombre interno del servicio.
  - CORS permite `http://localhost:3000`.
  - La cookie de sesión mantiene `HttpOnly`, `Secure` y `SameSite=None`. El compose se abre por `http://localhost`, que el browser trata como contexto seguro.

  Variables:
  - Valores reales en `.env` (no versionado). Nombres y placeholders en `.env.example`. Compose los carga con `env_file`.
  - Claves: `POSTGRES_DB`, `POSTGRES_PASSWORD`, `APP_DB_USER`, `APP_DB_PASSWORD`, `MIGRATION_DB_USER`, `MIGRATION_DB_PASSWORD`, `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`.
  - `DATABASE_URL` usa el rol de la app (solo DML). `MIGRATION_DATABASE_URL` usa el rol de Alembic (DDL).
  - Los secretos no van en la imagen ni en instrucciones `ENV` del Dockerfile.

  Tests que necesitan Postgres corren contra el servicio `db`. La suite no sustituye Postgres por otro motor.
