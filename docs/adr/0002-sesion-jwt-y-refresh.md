# ADR 0002: Access JWT en memoria y refresh HttpOnly

- Status: aceptada
- Date: 2026-11-01

## Contexto

Hay que persistir sesión al recargar sin dejar el access token en `localStorage` (XSS). El UI corre en `:3000` y la API en `:8000` (orígenes distintos).

## Decision

- Access token: JWT HS256, 15 minutos, incluye el rol. Solo en memoria. Header `Authorization`.
- Refresh: 7 días, cookie HttpOnly, Secure, **SameSite=None** (Lax no viaja cross-origin). Path `/auth`. JavaScript no la lee.
- Al recargar: `GET /auth/me` con `withCredentials` emite un access nuevo.
- Refresh persistido y rotado en `refresh_sessions` (jti). `user.auth_revoked_at` invalida sesiones.
- Contraseñas: argon2id (defaults de la librería). Nunca se devuelve el hash.
- `JWT_SECRET` ≥ 32 caracteres; se rechazan placeholders débiles (`change-me`, etc.).

## Consecuencias

SameSite=Lax no es viable mientras UI y API estén en puertos distintos. El cookie Secure exige Contextoo seguro; Compose en `http://localhost` lo trata como tal. El access no sobrevive a un refresh de página hasta que `/auth/me` responda.
