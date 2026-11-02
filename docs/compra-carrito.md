# Compra, carrito y sells

Cada ítem de compra es una fila en `sells`. El carrito es el estado `en_carrito`. El pago es mock.

## Estados

`en_carrito`, `en_curso`, `en_viaje`, `esperando_retiro`, `completada`, `cancelada`, `reembolsada`.

## Transiciones

- Agregar al carrito → `en_carrito`
- Comprar ahora / checkout → `en_curso` (paga el mock, descuenta stock, acredita al vendedor). Si el stock queda en 0, la publicación pasa a pausada.
- Quitar del carrito → `cancelada` (sin stock ni saldo)
- Cancelar `en_curso` (comprador, antes de despachar) → `cancelada` (revierte stock y crédito)
- Envío: `en_curso` → `en_viaje` → `completada`
- Retiro: `en_curso` → `esperando_retiro` → `completada`
- Reembolso desde `en_viaje`, `esperando_retiro` o `completada` → `reembolsada` (revierte stock y crédito)

No se cruza envío con retiro. `cancelada` y `reembolsada` son terminales.

## Seguimiento y chat

Plan y contrato detallados: [seguimiento-chat.md](seguimiento-chat.md).

Las órdenes pagadas se siguen en `/compras` (comprador) y `/ventas` (vendedor). El carrito no entra.

- ETA mock: al pasar a `en_viaje` se guarda `eta_at = now + 48h`. Solo aplica a envío. Retiro no tiene ETA.
- Mensajes de texto (máx. 1000) entre comprador y vendedor/admin, solo si la orden no está `en_carrito`.
- `WS /ws`: primer frame `{ "type": "auth", "token" }`, luego `watch` / `unwatch` de un `sell_id`. Eventos `message`, `status`, `notification`.
- Si el destinatario está en `watch` de esa orden, recibe el evento en vivo y no se crea notificación. Si no, se persiste una notificación y se emite `notification` (campana y timbre en el cliente).
- Hub WS en memoria (un proceso).

## Contrato

- Publicación: `ships`, `pickup` (al menos uno).
- `POST /sells` carrito. `GET /sells`. `PATCH /sells/{id}` solo `en_carrito`.
- `GET /sells/{id}` ficha (no `en_carrito`). Incluye `eta_at`, `updated_at`, `can_manage`.
- `GET/POST /sells/{id}/messages`.
- `POST /sells/checkout` `{ payment_method, sell_ids?, items? }`.
- `POST /sells/{id}/transition` `{ status }`.
- `GET /notifications`. `POST /notifications/{id}/read`. `POST /notifications/read-all`.
- `GET /auth/me` incluye `balance`.
