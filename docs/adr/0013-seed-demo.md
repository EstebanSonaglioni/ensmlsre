# ADR 0013: Seed demo al levantar

- Status: aceptada
- Date: 2026-11-02

## Contexto

Quien clona el repo no debería tener que cargar a mano usuarios, fotos y 90 días de ventas para ver dashboard y tablas.

## Decision

Servicio Compose `seed` (después de `migrate`, antes de `backend`): `python -m app.seed`.

- Si existe `boss@mail.com`, no recrea filas; sí reatacha fotos de `backend/seed/products`.
- Usuarios fijos: `boss@mail.com` (admin), `ventas1@mail.com` / `ventas2@mail.com`, `compras1@mail.com` / `compras2@mail.com`. Clave `DEMO_PASSWORD` (default `mlsre-demo`), no aleatoria.
- Productos: nombre = stem del archivo; fotos copiadas al directorio de imágenes; repartidos entre los dos vendedores.
- Ventas completadas esparcidas en 90 días; también abiertas, canceladas, reembolsos, preguntas y mensajes.

`./scripts/up.sh` genera secretos de infra al azar y deja `DEMO_PASSWORD` en default.

## Consecuencias

Pytest siembra (o reusa) esos usuarios y no los borra al limpiar filas de test. Un volumen de Postgres viejo sin `boss@` se puede sembrar; uno que ya tiene a boss no duplica. Cambiar la clave demo no actualiza hashes ya persistidos.
