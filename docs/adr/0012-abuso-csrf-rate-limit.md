# ADR 0012: CSRF, rate limit y topes

- Status: aceptada
- Date: 2026-11-02

## Contexto

El refresh viaja en cookie cross-origin. El access va por header. Hay que limitar fuerza bruta y bodies enormes sin un Redis.

## Decision

- CSRF de doble envío **solo** en endpoints que autentican con la cookie de refresh (refresh y logout). Cookie `csrf_token` + header/JSON. El resto de la API usa `Authorization` y no mezcla esa cookie con el access.
- Login/register: 5 intentos/minuto por IP, contador **en memoria**.
- Rate limit también en endpoints sensibles (p. ej. mensajes 20/min).
- Body máximo 1 MB; timeout 30 s; página máxima 100 ítems.
- Headers: `x-content-type-options: nosniff`; CSP con nonce en el middleware de Next cuando el frontend existe.

## Consecuencias

El rate limit no se comparte entre réplicas ni sobrevive al restart. CSRF no aplica a `GET /sells` ni al resto con Bearer.
