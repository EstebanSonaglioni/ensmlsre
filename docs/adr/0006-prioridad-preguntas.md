# ADR 0006: Prioridad (criticidad) de preguntas

- Status: aceptada
- Date: 2026-11-02

## Contexto

El vendedor necesita una bandeja `/preguntas` que suba lo que más duele: tiempo sin respuesta **y** valor de la publicación. No hay un motor de SLA por ticket.

## Decision

El score **no se persiste**. En cada `GET /questions`:

- Pendiente: `wait_hours = (now UTC − created_at) / 3600`
- Respondida: `wait_hours = 0`
- `score = wait_hours + net_profit`

`net_profit` es el declarado **por unidad** en el producto (no × cantidad de una venta). Orden default: score descendente.

Filtros `pending` (default) | `answered` | `all`. Sort: `score`, `wait`, `net_profit`, `created_at`, `name`. Alcance = publicaciones que el viewer administra (vendedor o admin de tienda).

Preguntas y respuestas son texto plano (sin HTML). Quien administra la publicación no puede preguntar en esa ficha.

Detalle: `docs/preguntas-criticidad.md`.

## Consecuencias

Una pregunta vieja en un producto barato puede superar a una reciente en uno caro, y viceversa: las unidades de score mezclan horas y pesos. Cambiar `net_profit` del producto mueve el ranking de preguntas ya hechas. No hay umbral “urgente” persistido; la UI muestra el número.
