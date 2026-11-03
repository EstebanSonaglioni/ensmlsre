# ADR 0016: Preview de HackerRank por el puerto 3000

- Status: aceptada
- Date: 2026-11-02

## Context

El Preview de HR publica la UI en `:3000`. `:8000` no es una vista del browser embebido. Next se accede por un host proxy, no por `localhost`.

## Decision

- `npm start` en `frontend` es `next dev` en `0.0.0.0:3000` (HR no corre `next build`).
- `allowedDevOrigins` incluye `**.hackerrank.net`, `**.hackerrank.com`, `**.hrcdn.net`.
- El browser llama `/backend/*`; Next reescribe a `API_INTERNAL_URL` (`http://127.0.0.1:8000`).
- Cookie de refresh con `Path=/backend/auth` en `up-local.sh`. Compose sigue con `Path=/auth` y `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- CSP `connect-src` incluye `'self'`; `frame-ancestors` admite dominios HR (el Preview va en iframe).
- CORS lista `localhost` y regex de hosts HR.

## Consequences

Compose no cambia. WebSocket va a `wss://<preview>/backend/ws`. Grafana sigue solo en Compose.
