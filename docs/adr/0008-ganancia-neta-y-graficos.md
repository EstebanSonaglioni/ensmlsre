# ADR 0008: Ganancia neta declarada y gráficos con el mismo eje

- Status: aceptada
- Date: 2026-11-02

## Contexto

No hay costo de mercadería en el sistema. El vendedor quiere ver ganancia y monto en el tiempo sin un dashboard saturado de cards.

## Decision

`products.net_profit` lo carga el vendedor (por unidad, `>= 0`). No se deriva del precio. El comprador no lo ve.

En ventas `completada`: `sum(net_profit × quantity)` usando el `net_profit` **actual** del producto (no un snapshot al checkout). Corte temporal: `Sell.updated_at` UTC.

Serie `net_profit_series`: un punto por día del rango 7/30/90 (`amount`, `net_profit`, `cumulative`). UI: **un** gráfico dinero×tiempo (área = monto, línea = ganancia). El acumulado queda en la API y no se dibuja para no mezclar tres series.

Otras series con el mismo eje van juntas: top productos = barras monto vs ganancia; composición = dos pies (fulfillment y pago) en un card; pipeline de abiertas = conteos, no dinero.

`docs/ganancia-neta.md`, `docs/ganancia-neta-tiempo.md`, `docs/dashboard-graficos.md`.

## Consecuencias

Si el vendedor edita `net_profit` después de vender, el dashboard histórico cambia. Días sin ventas aparecen en 0 para que el eje X cubra todo el período.
