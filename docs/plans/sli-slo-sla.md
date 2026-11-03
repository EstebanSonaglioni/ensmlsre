# SLI, SLO y SLA de la API

Grafana provisiona el dashboard **API SLI / SLO / SLA** (carpeta MLSRE) desde los access logs JSON (`event=request`: `status`, `latency_ms`, `path`). `/health` no entra.

## Definiciones

| | Qué mide | Objetivo en este stack |
| --- | --- | --- |
| **SLI** | Disponibilidad: requests con `status < 500` / total. Latencia: requests con `latency_ms` ≤ umbral / total. También p50/p95/p99. | Lo que muestran los paneles “SLI” sobre el rango de tiempo del dashboard. |
| **SLO** | Meta interna. | 99.9 % disponibles; 99 % de requests ≤ **500 ms**. |
| **SLA** | Compromiso más holgado que el SLO. | 99.5 % disponibles; 95 % de requests ≤ **800 ms**. |

Error budget de disponibilidad: `1 − ((1 − disponibilidad) / (1 − objetivo))`. En 0 el presupuesto del período se agotó.

Los umbrales se cambian en las variables del dashboard (`slo_availability`, `sla_availability`, `slo_latency_ms`, `sla_latency_ms`).

## Uso

Grafana: `http://localhost:3001` (secundario `3011`). Dashboards → MLSRE → API SLI / SLO / SLA.

Hace falta tráfico real (o el log que Alloy ya está tailando). Explore → Loki `{job="backend"}` si un panel queda vacío.
