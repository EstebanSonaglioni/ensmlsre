# Buscador por nombre en el catálogo del comprador

El catálogo vive en `frontend/app/page.tsx` (`ProductList` con `mine=false`) y pide `GET /products`, paginado (máx. 100). El filtro va en el servidor: filtrar solo la página actual dejaría afuera coincidencias de otras páginas.

## API

En `list_products` agregar `q: str = Query("", max_length=100)`. Si `q.strip()` no está vacío:

- Bound parameter (sin concatenar SQL).
- Case-insensitive, substring (p. ej. `reme` encuentra `Remera`).
- Catálogo con `q` vacío queda igual: solo publicaciones no pausadas, `id` desc.
- No aplicar `q` a `GET /products/mine` (vista vendedor `/productos`).
- Escapar `%` y `_` del needle para que no funcionen como wildcards de LIKE.

## Frontend

En `frontend/app/product-list.tsx`, solo si `!mine`:

- `Input type="search"`, placeholder `Buscar por nombre`.
- Debounce ~300 ms; al cambiar el término, resetear `page` a 1.
- Pasar `q` en `listProducts`; omitir el param si está vacío.

Empty state existente: “No hay publicaciones para mostrar.”

## Tests (pytest)

- Happy: dos productos (`Remera`, `Pantalón`); `GET /products?q=reme` incluye solo la remera.
- Esquina: `q` que no matchea → `items` vacío, `total` 0.
- Esquina: producto pausado no aparece aunque el nombre coincida.
- Esquina: `q` vacío o solo espacios = catálogo sin filtrar por nombre.
