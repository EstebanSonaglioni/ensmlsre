# Plan: fixes del QA por API (2026-11-01)

Bugs encontrados contra `http://localhost:8000` con `vendedor1@mail.com` y `sonaglioni.enoc@gmail.com`.

## 1. Rol JWT vs membresía

**Bug:** login/`/auth/me` devolvían `comprador` aunque el usuario era `admin` de una tienda.

**Criterios**
- Given un usuario con membresía de tienda y `users.role=comprador`, when inicia sesión o llama `GET /auth/me`, then `role` en el body y en el access JWT es `vendedor`.
- Given un comprador sin tienda, when inicia sesión, then sigue siendo `comprador`.

**Plan**
- Al armar la sesión, si hay membresía y el rol persistido es comprador, promover a vendedor y commitear.
- Usar ese rol efectivo en login, registro (sin cambio) y `/me`.

## 2. Access token = cookie de refresh (7 días)

**Bug:** un solo JWT en JSON y cookie, expiración 7 días. `/auth/me` devolvía la cookie.

**Criterios**
- Given login o registro, when llega la respuesta, then `access_token` no es el valor de `refresh_token` y vence en 15 minutos.
- Given cookie HttpOnly válida, when `GET /auth/me`, then se emite un access nuevo (no se copia la cookie al JSON).
- Given logout con CSRF, when se usa el access anterior, then 401.

**Plan**
- JWT de access (`typ=access`, 15 min) y de refresh (`typ=refresh`, 7 días, cookie Path `/auth`).
- Authorization solo acepta access. Cookie de `/auth/me` y logout solo refresh.
- Logout invalida la sesión (refresh y access del usuario).

## 3. Listado de ventas sin fecha

**Bug:** `GET /sells?from=` se ignoraba.

**Criterios**
- Given ventas propias, when `GET /sells?as_seller=true&from=&to=` con fechas ISO, then solo entran las de ese rango (`created_at`).
- Given `from` posterior a `to` o fecha inválida, when se lista, then 422 `{ "detail": "Los datos enviados no son válidos" }`.

**Plan**
- Query `from` y `to` (date). Filtrar por `created_at`. Status sigue igual.

## 4. XSS en texto de pregunta

**Bug:** `POST /products/{id}/questions` persistía `<script>…</script>`.

**Criterios**
- Given un comprador, when pregunta o responde con tags HTML, then 422 y no se guarda.
- Given texto plano, when pregunta, then 201.

**Plan**
- Validar pregunta, respuesta y mensaje de orden: sin tags `<…>`.

## Fuera de alcance

- Dashboard sin conteo de preguntas pendientes.
- Catálogo anónimo.
- Hash argon2 (no salió como fallo de este flujo HTTP).
- Separar las dos cuentas de Kioskito en tiendas distintas.

## QA de cierre

Repetir el playbook `.cursor/rules/qa-api.mdc` contra `:8000` con los mismos vendedores y dos buyers nuevos. No borrar la DB.
