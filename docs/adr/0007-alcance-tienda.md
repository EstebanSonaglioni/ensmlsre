# ADR 0007: Alcance por membresía de tienda

- Status: aceptada
- Date: 2026-11-01

## Contexto

Hay admin de tienda y vendedores invitados. Un vendedor no debe ver ventas ni preguntas de otra tienda. El admin sí ve el union de las tiendas que administra.

## Decision

`store_memberships.role`: `admin` | `vendedor`.

Alcance de `GET /sells?as_seller=true`, `GET /dashboard`, `GET /questions`:

- vendedor: filas con `seller_user_id = yo`
- admin: esas **más** todas las de `store_id` donde soy admin (incluye ventas de otros)

Si alguien es admin de A y vendedor en B, ve el union. El comprador no entra a `/dashboard` ni `/preguntas`. Crear tienda o aceptar invitación pasa el `users.role` a `vendedor`.

## Consecuencias

Los tests de aislamiento son por membresía, no por “todos los sells de la DB”. El ranking `sellers` del dashboard solo se llena si el viewer es admin de alguna tienda.
