## Story
Como persona, quiero registrarme como comprador y entrar con email y contraseña, para usar la app con mi cuenta.

## Acceptance criteria
- [ ] Dado que no tengo cuenta, cuando envío un email y una contraseña válidos, entonces quedo adentro de la app como comprador.
- [ ] Dado que ese email ya está registrado, cuando intento registrarme, entonces veo un mensaje general de error y no entro.
- [ ] Dado que el email o la contraseña no son válidos, cuando intento registrarme, entonces veo un mensaje general de error y no se crea la cuenta.

## Plan
- Pantalla de registro con email y contraseña.
- Al enviar, se crea la persona como comprador y queda con sesión iniciada.
- Si falla (datos inválidos o email repetido), se muestra solo el mensaje general y no entra.
- Adentro, se ve que está autenticado como comprador.
- Siempre entra como comprador: esta historia no elige rol ni crea tienda.

## Out of scope
- Iniciar sesión de alguien que ya tiene cuenta (HU #2)
- Cerrar sesión
- Confirmar el email
- Convertirse en vendedor, crear tienda o invitaciones (HU #3–#5)
