## Story
Como persona registrada, quiero que mi cuenta siga existiendo cuando vuelvo, para no tener que registrarme de nuevo.

Requires: #1

## Acceptance criteria
- [ ] Dado que ya me registré, cuando vuelvo e inicio sesión con el mismo email y contraseña, entonces entro con esa cuenta.
- [ ] Dado que ya me registré, cuando vuelvo e intento registrarme otra vez con el mismo email, entonces veo un mensaje general de error y no se crea otra cuenta.
- [ ] Dado que me registré, cuando la app se detiene y vuelve a arrancar, entonces sigo pudiendo entrar con esa cuenta y no tengo que registrarme de nuevo.

## Plan
- Al registrarse, la persona queda guardada de forma que sobrevive a volver más tarde y a un rearranque.
- Iniciar sesión busca esa persona guardada, no una lista temporal.
- El email repetido se rechaza contra esas personas guardadas.
- No hay pantalla nueva: sirven registro e iniciar sesión.
- Quien entra es la misma cuenta de siempre: mismo email y rol.

## Out of scope
- Persistir ventas, comentarios u otros datos (no están en esta historia)
- Cerrar sesión
- Recuperar la contraseña
- Crear tienda o invitaciones (HU #3–#5)
- Consultar si la API está viva, lista o sana (HU #6–#8)
