# ADR 0004: Errores genéricos al cliente y log estructurado

- Status: aceptada
- Date: 2026-11-01

## Contexto

El cliente no debe ver stack ni datos internos. Operación necesita request_id, latencia y fallos de auth sin secretos en disco versionado.

## Decision

- Respuesta de error: HTTP adecuado y `{ "detail": "<mensaje en español>" }`.
- structlog JSON: `request_id`, `method`, `path`, `status`, `latency_ms`, `user_id` si hay. Sin passwords, tokens ni cookies.
- Excepciones inesperadas: ERROR con stack solo en servidor.
- Archivo `backend/var/logs/app.log` (gitignored).

## Consecuencias

El frontend solo muestra `detail`. Depurar un 403/422 exige el log, no el body. Los textos de error son deliberadamente genéricos para no filtrar existencia de usuarios o filas.
