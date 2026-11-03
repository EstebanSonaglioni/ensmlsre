# Perfil de usuario

Página `/perfil` para todos los usuarios autenticados.

- Nombre para mostrar y foto de perfil (opcional).
- Quien no vende todavía puede unirse a una tienda (invitación) o crear la propia.
- El catálogo (`/`) no muestra el formulario de crear tienda.

## API

- `GET /auth/me` incluye `display_name`.
- `PATCH /auth/profile` (Authorization, multipart): `display_name`, `image` opcional.
- `GET /auth/profile/image` (Authorization): foto, 404 si no hay.
