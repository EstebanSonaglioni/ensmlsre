## Story
Como persona registrada, quiero iniciar sesión, para volver a entrar con mi cuenta.

Requires: #1

## Acceptance criteria
- [ ] Dado que ya tengo cuenta y no estoy adentro, cuando envío el email y la contraseña de esa cuenta, entonces quedo adentro con mi cuenta.
- [ ] Dado que el email no está registrado o la contraseña no es la de esa cuenta, cuando intento entrar, entonces veo un mensaje general de error y no entro.
- [ ] Dado que el email o la contraseña no son válidos, cuando intento entrar, entonces veo un mensaje general de error y no entro.

## Plan
- Pantalla para entrar con email y contraseña.
- Con los datos de una cuenta ya registrada, la persona queda adentro con esa cuenta.
- Si no hay cuenta, la contraseña no coincide o los datos no son válidos, se muestra solo el mensaje general y no entra.
- Este camino no crea una cuenta nueva.
- Quien entra es la misma persona que ya se registró.

## Out of scope
- Registrarse (HU #1)
- Cerrar sesión
- Recuperar la contraseña
- Crear tienda o invitaciones (HU #3–#5)
- Consultar si la API está viva, lista o sana (HU #6–#8)
