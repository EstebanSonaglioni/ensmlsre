# ADR 0003: Dos roles de Postgres y bind en loopback

- Status: aceptada
- Date: 2026-11-01

## Contexto

La app no debe poder hacer DDL. El superusuario de la imagen solo inicializa el cluster. Postgres no debe quedar expuesto a la LAN.

## Decision

- Rol de aplicación: solo DML. `DATABASE_URL` lo usa.
- Rol de migraciones: DDL. `MIGRATION_DATABASE_URL`; el servicio `migrate` corre `alembic upgrade head` y termina.
- Init en `docker/postgres/init/` crea ambos roles (solo con volumen vacío).
- Publicación en el host: `127.0.0.1:${POSTGRES_HOST_PORT}:5432`.

## Consecuencias

Si se cambia la clave del rol con un volumen ya creado, hay que `docker compose down -v` o alinear el rol a mano. Tests contra el mismo Postgres de Compose, no contra SQLite.
