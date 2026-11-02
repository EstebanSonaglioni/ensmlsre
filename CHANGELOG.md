# Changelog

## 2026-11-02

- Puertos del host configurables (`FRONTEND_PORT`, `BACKEND_PORT`, `GRAFANA_PORT`, `POSTGRES_HOST_PORT`) con valores secundarios si los default están ocupados.
- README con los pasos para clonar, armar `.env` y levantar el stack con Compose.
- Logs JSON a `var/logs/app.log`; Alloy los manda a Loki y Grafana los muestra en `:3001`.

## 2026-11-01

- Access JWT de 15 minutos distinto de la cookie HttpOnly de refresh (7 días); `/auth/me` emite un access nuevo.
- Login y `/auth/me` corrigen a `vendedor` si el usuario ya tiene membresía de tienda.
- `GET /sells` filtra por `from`/`to` (fecha de creación).
- Preguntas, respuestas y mensajes de orden rechazan HTML.
- Bandeja `/preguntas` para vendedores, ordenada por criticidad (horas sin respuesta + ganancia neta).
- Preguntas de la ficha y ventas confirmadas llegan por WebSocket; si no estás en esa pantalla, entran a la campana.
- El dashboard muestra la cantidad de ventas canceladas del período.
- Pytest ya no deja publicaciones en el Postgres de compose: las fotos van a un directorio de test y las filas se revierten al terminar.
- Cuenta en el header: un círculo con foto o inicial que abre perfil, nombre, mail y cerrar sesión.
- Quien publica o administra un producto no puede preguntar en esa ficha; solo compradores ajenos.
- Perfil con nombre y foto; el comprador se habilita como vendedor desde ahí (invitar o crear tienda), no desde el catálogo.
- Cada publicación declara ganancia neta por unidad; el dashboard suma esa ganancia en las ventas completadas.
- Dashboard de vendedores: ventas completadas, monto, top productos y ranking de la tienda para el admin (`GET /dashboard`).
- En la ficha, la imagen queda cuadrada y no supera la mitad del alto de la pantalla.
- Las tarjetas de producto no muestran el id.
- El comprador busca publicaciones por nombre en el catálogo (`GET /products?q=`).
- El catálogo del comprador vuelve a mostrar las fotos: se resuelven en el directorio de imágenes de la app.
- El listado de ventas es una tabla; el estado usa warning, info, accent o danger según STYLE.md.
- El campo para escribir el mensaje queda al pie del panel de chat.
- En el chat de la orden, los mensajes propios van a la derecha y los del otro usuario a la izquierda.
- El plan de seguimiento, chat y notificaciones quedó en `docs/seguimiento-chat.md`.
- Seguimiento de órdenes para comprador y vendedor, chat en vivo por WebSocket, campana de notificaciones y timbre si no está en la ficha.
- Las tarjetas de producto tienen el mismo tamaño, 5px de padding y la foto centrada.
- En la vista de comprador, las fotos son cuadradas y no superan un cuarto del alto de la pantalla.
- La imagen es obligatoria al publicar; las publicaciones existentes reciben una foto.
- En la ficha del vendedor, la imagen es cuadrada y no supera la mitad del alto de la pantalla.
- Si una compra deja el stock en 0, la publicación se pausa sola.
- Compra mock con carrito y tabla `sells`: estados, stock, crédito al vendedor y sin débito al comprador.
- El precio de los productos se muestra con el signo `$` adelante.
- Al guardar un producto aparece un toast de confirmación; las invitaciones pendientes salen del catálogo y de `/tienda` hasta el menú de perfil.
- El inicio es el catálogo de cliente; `/productos` lista solo las propias (`GET /products/mine`) y el menú de tienda/productos queda para vendedores. El estado Pausado usa el color warning.
- En la ficha, el vendedor o admin edita los campos a la vista y puede eliminar la publicación (`DELETE /products/{id}`).
- Cada publicación se abre en `/productos/[id]` para ver estado, editarla, pausarla y atender preguntas (`PATCH /products/{id}`).
- El panel se parte en `/tienda` y `/productos`, con esas entradas en el menú lateral.
- Publicaciones de productos: alta con imagen, listado/ficha, pausa/reanuda y preguntas/respuestas.
- Un invitado puede aceptar la invitación y pasar a vender en esa tienda.
- Logout: `POST /auth/logout` revoca el token, borra la cookie y el panel tiene «Cerrar sesión».
- El frontend aplica `STYLE.md`: canvas dark, cards elevadas, tokens shadcn y layout con sidebar.
- Las tiendas y quién las administra se guardan en Postgres (`stores`, `store_memberships`).
- El admin de una tienda puede invitar a vender por email; el invitado ve la invitación al entrar (`POST`/`GET /stores/invitations`).
- Quien está autenticado puede ver las tiendas asociadas, con búsqueda y paginación (`GET /stores`).
- La sesión persiste al recargar: el backend guarda el token en una cookie HttpOnly y el frontend la restaura con `/auth/me`.
- Un comprador puede crear una tienda con un nombre único y pasar a administrarla.
- Inicio de sesión: quien ya tiene cuenta entra con email y contraseña; si falla, ve un mensaje general.
- Estilos del frontend: Tailwind CSS y shadcn/ui.
- Postgres queda publicado en `localhost:5433` para consultar la base desde la máquina.
- Inicialización del proyecto base: API FastAPI con `GET /health`, Next.js vacío, Compose (db, migrate, backend, frontend) y variables de entorno.
