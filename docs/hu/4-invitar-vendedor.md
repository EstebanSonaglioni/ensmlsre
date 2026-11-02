## Story
Como admin de una tienda, quiero invitar a alguien a vender en ella, para sumar vendedores.

Requires: #3

## Acceptance criteria
- [ ] Dado que administro una tienda, cuando invito a alguien con un email, entonces queda una invitación a esa tienda para esa persona.
- [ ] Dado que me invitaron, cuando entro con ese email, entonces veo la invitación en la app (no llega un correo).
- [ ] Dado que el email no es válido, cuando intento invitar, entonces veo un mensaje general de error y no se crea la invitación.

## Plan
- Quien ya administra una tienda puede invitar con un email.
- Al enviar, queda la invitación a esa tienda para esa persona.
- Esa persona, al estar adentro con ese email, ve la invitación en la web. No se manda un mail.
- Si el email no es válido, se muestra solo el mensaje general y no se invita.
- Aceptar la invitación no entra acá.

## Out of scope
- Aceptar la invitación (HU #5)
- Enviar un correo
- Crear la tienda (HU #3)
- Cerrar sesión
- Catálogo, ventas o comentarios
