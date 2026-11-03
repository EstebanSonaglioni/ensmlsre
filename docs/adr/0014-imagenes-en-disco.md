# ADR 0014: Imágenes de producto en disco

- Status: aceptada
- Date: 2026-11-01

## Contexto

No hay object storage. Las fotos tienen que sobrevivir al contenedor vía bind mount y no ir a Postgres.

## Decision

`PRODUCT_IMAGES_DIR` (default `var/product-images`). Alta de publicación: bytes validados (jpeg/png/gif, tope de upload), nombre de archivo aleatorio. El seed demo usa el **nombre original** (`aceite.jpeg`) para que coincida con el producto.

`GET /products/{id}/image` sirve el archivo si el viewer puede ver la publicación. Avatares análogo en `PROFILE_IMAGES_DIR`.

## Consecuencias

Borrar la fila borra el archivo. Tests apuntan a un directorio propio para no dejar fotos en el volumen de compose. Sin backup aparte del bind mount.
