# Dashboard de métricas para vendedores

Página `/dashboard` (solo vendedores). El comprador no entra.

## Qué cuenta

Solo filas `sells` con `status = completada`. Carrito, canceladas, reembolsos y órdenes en curso no suman a ventas realizadas ni al monto.

Período: selector 7 / 30 / 90 días (default 30). El corte es `Sell.updated_at >= now - N days` (UTC), el momento en que pasó a `completada`. Query `days` ∈ {7, 30, 90}.

## Alcance

Igual que `GET /sells?as_seller=true`:

- vendedor (no admin): `seller_user_id = yo`
- admin de una tienda: todas las ventas de esas tiendas (incluye otros vendedores)

Si alguien es admin de A y vendedor en B, ve el union.

## API

`GET /dashboard?days=30` con JWT. 403 si no hay membresía de tienda. 422 si `days` no es 7, 30 o 90.

Respuesta:

- `days`, `from` (ISO)
- `sales_count`, `total_amount`, `net_profit_total`, `units_sold`, `average_ticket` (0 si no hay ventas)
- `open_orders`: snapshot sin período (`en_curso`, `en_viaje`, `esperando_retiro`)
- `cancelled_count` en el período (`status = cancelada`)
- `refunded_count` / `refunded_amount` en el período
- `top_products`: hasta 10 por unidades; incluye `net_profit` (suma `net_profit` del producto × cantidad)
- `sellers`: hasta 10 por monto, solo si el viewer es admin de alguna tienda; si no, lista vacía
