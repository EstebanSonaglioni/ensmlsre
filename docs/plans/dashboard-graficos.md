# Gráficos extra del dashboard

En `/dashboard` (y la serie de tiempo también en `/ventas`). Métricas con el **mismo eje** van juntas.

## Dinero × tiempo (un gráfico)

`net_profit_series`: por día UTC, ventas `completada`:

- `amount`: suma de `subtotal` (monto vendido)
- `net_profit`: `net_profit del producto × quantity`
- `cumulative`: ganancia neta corrida

UI: área gris = monto; línea verde = ganancia neta. El acumulado no se dibuja.

## Conteos de snapshot (un gráfico)

`open_by_status`: `en_curso`, `en_viaje`, `esperando_retiro` (igual que `open_orders`, sin filtro de `days`).

## Composición de ventas completadas (un card, dos pies)

Ambos sobre `completada` del período, eje dinero:

- `fulfillment_mix`: envío vs retiro (`count`, `amount`)
- `payment_mix`: medio de pago (`count`, `amount`)

## Top productos

Misma lista `top_products`: barras agrupadas monto vs ganancia neta (mismo eje $), más la tabla.
