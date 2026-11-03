# ADR 0011: SLI/SLO/SLA con Alloy, Loki y Grafana

- Status: aceptada
- Date: 2026-11-02

## Contexto

No hay APM externo. El log JSON de cada request alcanza para disponibilidad y latencia.

## Decision

Alloy taila `app.log` → Loki → Grafana (`:3001`). Dashboard provisionado **API SLI / SLO / SLA** (`docs/sli-slo-sla.md`). `/health` no entra al SLI.

- SLO interno: 99.9 % disponibles; 99 % ≤ 500 ms.
- SLA más holgado: 99.5 %; 95 % ≤ 800 ms.

Error budget a partir de la disponibilidad del rango. Sin alertas push.

## Consecuencias

Hace falta tráfico (o el log ya taileado) para ver paneles. La retención de logs es operativa: no se versionan ni llevan secretos.
