# Filtros de ventas y delta del dashboard

## Ventas (`/ventas`)

`GET /sells?as_seller=true` ya filtra `status`, `from`, `to`. Se agrega `q` (email del comprador, máx. 100).

UI: estado (sin `en_carrito`), rango de fechas, buscador de comprador. `/compras` no cambia.

## Dashboard

Ventana actual: `[now - days, now)`. Anterior: `[now - 2*days, now - days)`.

`previous`: ventas, monto, ganancia, unidades, ticket y canceladas. `delta.*_pct`: variación % o `null` si el anterior es 0 (la UI no muestra “nuevo”).

`open_orders` sigue siendo snapshot, sin delta.
