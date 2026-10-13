# Estado final del laboratorio OpenTelemetry

Consolidado: 2026-10-12 20:59 America/Bogota. Cierre del desarrollo local. Implementado y validado localmente. Infraestructura AWS/GCP preparada y validada por Terraform; **ningún recurso cloud desplegado**, ninguna imagen publicada y ningún terraform plan/apply contra cuentas ejecutado.

Preparación documental para GitHub: 2026-10-13, America/Bogota. El repositorio dispone de Git. Se actualizan únicamente `.gitignore`, `GUIA_LOCAL.md` y este estado; no se ejecutan pruebas de carga ni se cambian resultados o evidencias. El PDF local queda excluido de Git: el informe definitivo se está editando en Google Docs y las etapas AWS/GCP siguen pendientes.

## Resultados comprobados

- Pruebas: 10/10 (ocho originales y dos nuevas), con advertencias de deprecación de TestClient. Evidencia: tests.txt.
- Integración: 13/13 comprobaciones; CRUD, 404/422, persistencia al reiniciar B, trace A/B/PostgreSQL, logs Loki vía Grafana, targets Prometheus y seis paneles. Evidencia: validation.json, trace.json, logs.json, targets.json y dashboard-queries.json.
- Imágenes cloud: cinco construidas y bundle de ocho contenedores probado en Docker local (CRUD, traza, gateway, targets y Grafana). Evidencias cloud-image-builds.json/cloud-bundle-local.json; contenedores de prueba detenidos. No es despliegue cloud.
- Capturas reales: jaeger-trace.png, grafana-dashboard.png y grafana-logs.png, inspeccionadas visualmente.
- Falla controlada: B detenido, A devuelve 503 y B se restaura; failure.json.
- Benchmark: 50 VUs, cinco minutos por modo y warm-up 20s; datos sintéticos compartidos, 1 CPU/512 MiB por app. Dos parejas ejecutadas: la exploratoria se conserva en evidence/exploratory y la pareja final se ejecutó sin instalaciones/builds/validaciones de infraestructura simultáneos.
- Terraform AWS: valid=True; GCP: valid=True. init sin backend y validate; evidencia terraform-*-validate.json e init.txt. Validar esquema no demuestra despliegue.

## Cierre local: correlación y escenarios k6

La correlación entre Grafana, Jaeger y Loki quedó validada. La configuración efectiva de Grafana conserva las plantillas logs→trazas y trazas→logs; la consulta a Jaeger mediante Grafana y la consulta LogQL con el mismo trace_id devolvieron la traza y registros de service-a y service-b. Trace ID: `868d7e4a569d404cb1dcfa718703ab90`. Evidencia: `docs/evidence/reference/correlation-runtime.json`. Esta validación corresponde al provisioning y las consultas reales a los backends; no acredita navegación automatizada de exemplars.

| Escenario k6 | Carga validada | Exit | Resultado |
|---|---|---:|---|
| Normal | 10 VUs, 20 s, 378 solicitudes | 99 | Comprobaciones funcionales aprobadas; p99 1241.05 ms incumplió el umbral menor de 1000 ms |
| Errores | 10 VUs, 20 s, 376 solicitudes | 0 | Cumplió los umbrales definidos; 404/422 intencionales tratados como respuestas esperadas |
| Pico | 10→20→10 VUs, 30 s, 922 solicitudes | 0 | Cumplió los umbrales definidos |

Los tres escenarios aprobaron el 100% de las comprobaciones funcionales y tuvieron cero respuestas inesperadas. Normal cumplió p95 menor de 500 ms, pero incumplió p99; por eso exit 99 no se presenta como éxito global. Errores y pico no imponían un umbral de latencia p99. Evidencias: `docs/evidence/reference/k6-scenarios.json`, `k6-normal.json`, `k6-errors.json` y `k6-spike.json` en la misma carpeta.

Estas ejecuciones cortas son validaciones de escenarios y no reemplazan la pareja de benchmark de 50 VUs y cinco minutos por modo. Los resultados del benchmark, sus JSON, logs y CSV se mantienen sin modificar. En el cierre del desarrollo local se actualizaron este estado y el borrador PDF: no se ejecutaron nuevos benchmarks, no se cambió la arquitectura, no se hizo push a GitHub y no se desplegó AWS ni GCP. La preparación documental posterior mantiene ese cierre y reserva el PDF local; los despliegues siguen pendientes de autorización.

## Benchmark final

| Medición | Sin SDK OTel | Con SDK OTel | Diferencia |
|---|---:|---:|---:|
| p99 HTTP k6 (ms) | 680.39 | 2026.96 | +1346.56 ms (+197.91%) |
| CPU A+B (% de un core, media) | 143.74 | 165.91 | +22.16 puntos (+15.42%) |
| Memoria A+B (MiB, media) | 173.25 | 199.03 | +25.78 MiB (+14.88%) |
| Requests | 24784 | 16396 | Carga de VUs constante, throughput variable |
| Tasa errores HTTP | 0.0000% | 0.0000% | Umbral k6: menos de 1% |
| CPU Collector (% de un core) | 0.38 | 1.97 | Separado del overhead A+B |
| Memoria Collector (MiB) | 77.85 | 94.14 | Separada de memoria A+B |

Mediciones de Docker stats promediadas por servicio y sumadas para A/B; ver CSV para cantidad exacta de muestras. CPU % de un core no es porcentaje del host completo. Con/sin mantiene /metrics, logs stdout y dependencias SDK importadas: compara instrumentación/exportación SDK activa frente a desactivada. Collector encendido en ambos modos, inactivo respecto de aplicaciones en baseline. Se restauró OTEL_ENABLED=true al terminar.

Una pareja final, orden sin→con y workload GET/PUT sobre el mismo crédito. No es un intervalo de confianza ni demuestra overhead general para todas las cargas. El primer par coincidió con preparación de Terraform y quedó etiquetado exploratorio. Los valores pueden variar por carga del host Docker/Windows, caché y orden. Todos los PUT comparten fila y pueden crear contención; no representa todas las cargas de créditos. No se inventan resultados cloud ni promesas de latencia.

## Matriz de requisitos

| Requisito | Implementado/probado | Evidencia/archivo | Pendiente, riesgo y siguiente paso |
|---|---|---|---|
| Contratos de créditos y /metrics | Sí, tests y CRUD real | app/main.py, service.py, tests.txt | Memoria solo fallback; Compose usa B |
| Dos microservicios + PostgreSQL | Sí, HTTP A→B y DB persistente | app/storage.py, compose.otel.yml, validation.json | No migración automática del diccionario histórico |
| SDK auto + spans propios | Sí, FastAPI/httpx/SQLAlchemy y credit.* | app/telemetry.py, trace.json | Mantener versiones compatibles |
| TraceContext W3C | Sí, trace_id común 868d7e4a569d404cb1dcfa718703ab90 | trace.json y logs.json | Repetir en cada nube autorizada |
| Tres señales | Sí, OTLP trazas/métricas/logs | Collector, Loki, SDK y targets | Logs uvicorn no estructurados ni exportados como negocio |
| Collector completo/versionado | Sí, local; grpc/http y 3 pipelines | otel/collector.yaml, collector.txt | Despliegue en ambas nubes pendiente de autorización |
| Jaeger, Prometheus, Grafana, Loki | Sí, APIs y provisioning | targets.json, validation.json | Datos de Jaeger en memoria; exportar antes de reinicio |
| Dashboard seis paneles | Sí, provisioning y queries ejecutadas | dashboard.json, dashboard-queries.json | Cero eventos Collector puede no crear serie; fallback cero documentado |
| Correlación Grafana/Jaeger/Loki | Validada: configuración efectiva y consultas con mismo trace_id en A/B | reference/correlation-runtime.json, logs.json, trace.json | Exemplars no verificados automáticamente |
| k6 normal, errores y pico | Errores/pico cumplen umbrales; normal exit 99 por p99, funcionalidad aprobada | reference/k6-scenarios.json y k6-*.json | Normal no cumple objetivo p99; ejecuciones cortas, sin conclusión estadística |
| Benchmark p99/CPU/memoria | Sí, 2 pares, final comparable en setup | benchmark.json, summaries, CSV | Repetir varias veces y alternar orden para estadística |
| Falla controlada | Sí, A 503 cuando B no disponible | failure.json | No es un benchmark de fallas de cinco minutos |
| IaC AWS/GCP | Sí, Terraform validate local | infra/aws y infra/gcp, lockfiles | Cuotas/IAM/costos/imágenes/arranque remoto sin probar |
| Collector desplegado AWS/GCP | No | docs/NUBES_COSTOS_Y_ELIMINACION.md | Obtener autorización del plan antes de desplegar |
| Requisitos de la profesora | oTelLabs.zip revisado sin extracción ni modificación; original conservado localmente | docs/evidence/reference/zip-inventory.json | Confirmar rúbrica ponderada y bundle vs servicios separados; referencia GCP usa GKE |
| Reporte ≥5 páginas | Borrador local de seis páginas conservado; informe definitivo en edición | INFORME_LAB_OTEL.pdf local; informe definitivo en Google Docs | PDF excluido de Git; completar informe definitivo y etapas AWS/GCP antes de su publicación |
| Repositorio para entrega | Git disponible; exclusiones de entrega preparadas | README, .gitignore y docs/evidence/README.md | No se ejecutaron git add, commit ni push; publicación pendiente |

## Archivos y ejecución

Cambios: app/main.py, app/service.py, requirements.txt, README.md y .gitignore; nuevos app/storage.py, app/telemetry.py, compose.otel.yml, .env.example, .dockerignore, tests/test_remote.py, otel/, scripts/, infra/aws/, infra/gcp/, infra/images/ y docs/. Los componentes anteriores, incluidos Compose y monitoreo históricos, workflows, Jenkins y manifiestos anteriores, se conservan físicamente y quedan excluidos de Git. El repositorio dispone de Git; esta preparación no modifica el índice ni crea commits.

Puertos locales: API 18000, Jaeger 16686, Prometheus 19090, Grafana 13000, OTLP 14317/14318, todos en loopback. Monitoreo anterior 3000/9090 intacto. Grafana lab/local-lab-only solo local.

Comandos reproducibles: `docker compose -f compose.otel.yml up -d --build --wait`, `python scripts/validate_local.py`, `python scripts/validate_failure.py`, `python scripts/benchmark.py`, `powershell -NoProfile -File scripts/validate_infra.ps1`. Ver GUIA_LOCAL.md para detalles y snapshots disponibles. Detener con `docker compose -f compose.otel.yml stop`; no eliminar volúmenes sin permiso.

Línea base host falló antes de ejecutar tests por falta de prometheus_client. La suite pasó dentro de Docker. Terraform primero tuvo un problema PowerShell con stderr, luego timeout del provider sobre bind mount Windows; se corrigió usando un volumen Linux dedicado. Esos fallos no se ocultan ni se consideran pruebas exitosas. Los errores anteriores están conservados donde corresponde en evidence.

## Nubes: recursos, costos y eliminación

AWS: tarea Fargate 2vCPU/4GiB, RDS 20GiB, VPC/subnets/SG/IPv4, seis ECR, Logs y Secrets/IAM. Fargate ≈US$0.0987/h solo cómputo. Google: Cloud Run 8vCPU/4GiB activo, Cloud SQL 10GiB, registry, secretos, logs/IAM; Cloud Run ≈US$0.5472/h solo cómputo. DB, disco, logs, secretos y transferencias son adicionales; créditos gratuitos sin verificar. Detalle y fuentes: NUBES_COSTOS_Y_ELIMINACION.md.

La eliminación requiere aprobación y plan -destroy; borrar solo imágenes propias si bloquean registries y revisar secretos/snapshots residuales. Bases de datos sin protección de borrado: exportar créditos primero. No se ejecutó eliminación ni despliegue cloud. Trabajo remoto pendiente: confirmar equivalencia con la referencia de la profesora, elegir duración/presupuesto/región y obtener autorización de un plan concreto.

## Informe definitivo y publicación pendiente

El informe definitivo está siendo editado en Google Docs. El PDF local y el HTML anterior se conservan, pero quedan excluidos de Git. Las fuentes documentales anteriores no sustituyen el informe definitivo. AWS y GCP todavía no se han desplegado y requieren autorización previa.

El material docente fue revisado y permanece en `referencias/oTelLabs.zip`, excluido de Git; su inventario histórico conserva la ruta original de la revisión. El laboratorio local no depende de instrucciones del asistente. El índice `docs/evidence/README.md` y sus enlaces permanecen intactos, al igual que todos los resultados, JSON/CSV, capturas y manifiestos históricos de hashes.

La documentación debe utilizar únicamente las pruebas y mediciones guardadas y distinguir validación local e infraestructura preparada de despliegues reales. Esta preparación no ejecutó git add, commit, push ni acciones cloud.
