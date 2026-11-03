# Architecture Decision Records

Decisiones de diseño que no conviene re-litigar en cada cambio. El detalle operativo vive en `docs/*.md` y las reglas de implementación en `AGENTS.md`.

| ADR | Tema |
| --- | --- |
| [0001](0001-stack-local-compose.md) | Stack y arranque local con Compose |
| [0002](0002-sesion-jwt-y-refresh.md) | Access JWT en memoria y refresh HttpOnly |
| [0003](0003-postgres-dos-roles.md) | Roles DML vs DDL y Postgres en loopback |
| [0004](0004-errores-y-logs.md) | Errores al cliente y log estructurado |
| [0005](0005-maquina-estados-compras.md) | Máquina de estados de `sells` |
| [0006](0006-prioridad-preguntas.md) | Score de criticidad de preguntas |
| [0007](0007-alcance-tienda.md) | Aislamiento por membresía de tienda |
| [0008](0008-ganancia-neta-y-graficos.md) | Ganancia neta declarada y ejes de gráficos |
| [0009](0009-catalogo-sin-pii.md) | Catálogo público sin PII ni ganancia |
| [0010](0010-websocket-en-memoria.md) | Chat y notificaciones por WS in-process |
| [0011](0011-sli-loki-grafana.md) | Observabilidad SLI/SLO/SLA |
| [0012](0012-abuso-csrf-rate-limit.md) | CSRF, rate limit y tope de body |
| [0013](0013-seed-demo.md) | Usuarios y datos demo al levantar |
| [0014](0014-imagenes-en-disco.md) | Fotos de producto en filesystem |
| [0015](0015-arranque-host-sqlite.md) | Arranque en host con SQLite (sin Docker) |

Estado: **aceptada**, salvo que el ADR diga lo contrario.
