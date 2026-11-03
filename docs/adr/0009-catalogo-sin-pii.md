# ADR 0009: Catálogo y WS públicos sin PII ni ganancia

- Status: aceptada
- Date: 2026-11-02

## Contexto

La ficha y el listado los ve cualquier sesión (comprador). `seller_email`, `asker_email` y `net_profit` son internos del vendedor.

## Decision

Schemas públicos de producto/pregunta no incluyen esos campos. El vendedor los ve al administrar (alcance de membresía). Eventos WS hacia watchers de ficha pública tampoco los mandan.

Emails se validan con EmailStr y se normalizan (trim + lower).

## Consecuencias

Cualquier cliente que parseaba `seller_email` en el catálogo deja de recibirlo. La bandeja de preguntas del vendedor sí identifica Contextoo de producto, no el mail del asker en el catálogo público.
