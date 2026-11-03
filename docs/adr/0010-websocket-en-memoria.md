# ADR 0010: WebSocket in-process para chat y notificaciones

- Status: aceptada
- Date: 2026-11-01

## Contexto

Hace falta chat de orden y “la ficha se actualiza sola”, más campana si el usuario no está mirando. Un broker (Redis) es más de lo que el stack local pide.

## Decision

- Un hub en memoria en el proceso Uvicorn.
- `WS /ws`: primer frame `{ "type": "auth", "token" }`; luego `watch`/`unwatch` de `sell_id` o `product_id`.
- Origin alineado a CORS. Si el destinatario está en `watch` de esa entidad, llega el evento y **no** se crea notificación (salvo venta nueva, que siempre campanea).
- Si no está en la ficha: fila en `notifications` + evento `notification` (badge y beep).
- Chat: texto plano, máx. 1000. Sin adjuntos.

`docs/seguimiento-chat.md`.

## Consecuencias

Varias réplicas de backend no comparten el hub. `--reload` puede dropear conexiones. No hay push OS ni mail.
