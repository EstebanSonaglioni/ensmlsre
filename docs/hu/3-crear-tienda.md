## Story
Como comprador, quiero crear mi propia tienda, para pasar a vender y administrarla.

Requires: #1

## Acceptance criteria
- [ ] Dado que estoy adentro como comprador, cuando creo una tienda con un nombre que no existe, entonces queda creada y paso a venderla y administrarla.
- [ ] Dado que ese nombre de tienda ya existe, cuando intento crear la tienda, entonces veo un mensaje general de error y no se crea.
- [ ] Dado que el nombre no es válido, cuando intento crear la tienda, entonces veo un mensaje general de error y no se crea.

## Plan
- Quien ya está adentro como comprador ve cómo crear una tienda con un nombre.
- Al enviarlo, la tienda queda con ese nombre y la persona pasa a venderla y administrarla.
- Si el nombre está repetido o no es válido, se muestra solo el mensaje general y no se crea.
- Esta historia no invita a nadie ni acepta invitaciones.
- Un nombre alcanza: no se pide más datos de la tienda.

## Out of scope
- Iniciar sesión (HU #2)
- Invitar vendedores (HU #4)
- Aceptar una invitación (HU #5)
- Cerrar sesión
- Catálogo, ventas o comentarios
