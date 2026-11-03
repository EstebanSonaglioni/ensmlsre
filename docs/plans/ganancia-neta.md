# Ganancia neta por unidad

Campo declarado por el vendedor al publicar (no se calcula desde el precio). En publicaciones viejas queda `0`. El comprador no lo ve en la tarjeta ni en la ficha.

## Persistencia

`products.net_profit` `Numeric(12, 2)`, default `0`.

## API

Create y PATCH: Form `net_profit` opcional, default `"0"`. Decimal `>= 0`. `ProductItem` incluye `net_profit`.

## Dashboard

Para ventas `completada` del período: `net_profit_total = sum(net_profit * quantity)`.
En `top_products`, `net_profit` es esa suma por producto.
