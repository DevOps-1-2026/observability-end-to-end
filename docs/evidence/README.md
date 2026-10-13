# Índice de evidencias del laboratorio OpenTelemetry

Este índice organiza las evidencias existentes del laboratorio de créditos en FastAPI. Los enlaces son relativos a `docs/evidence/` y corresponden a archivos reales. Las evidencias registran ejecuciones anteriores: crear este índice no ejecutó pruebas, benchmarks ni despliegues y no modificó capturas o resultados.

La cadena comprobada es **Service A → HTTP → Service B → PostgreSQL**. Las tres señales se consultan en Jaeger, Prometheus y Loki, con Grafana como interfaz. El trace_id de la integración es `868d7e4a569d404cb1dcfa718703ab90`.

## Arquitectura e instrumentación

| Evidencia | Qué demuestra |
|---|---|
| [compose-ps.txt](compose-ps.txt) | Snapshot de los ocho servicios locales, sus imágenes y puertos; A, B y PostgreSQL aparecen saludables. No representa el estado actual del equipo. |
| [dependencies.txt](dependencies.txt) | Versiones instaladas de FastAPI, SDK OpenTelemetry 1.38.0, instrumentadores 0.59b0, httpx, SQLAlchemy y psycopg. La instalación por sí sola no acredita exportación. |
| [collector.txt](collector.txt) | Arranque del Collector 0.139.0, memory limiter, receptores OTLP gRPC/HTTP y estado ready. Las señales recibidas se acreditan con trazas, métricas y logs. |
| [trace.json](trace.json) | Instrumentación HTTP y PostgreSQL, recursos service-a/service-b y spans propios `credit.create` y `credit.persist` dentro de una misma traza. |
| [artifact-validation.json](artifact-validation.json) | Validación guardada de salud de A/B con OTel activo y comprobaciones de artefactos. Su hash del PDF corresponde al momento de esa validación, no certifica versiones posteriores del informe. |

## Trazas distribuidas en Jaeger

| Evidencia | Qué demuestra |
|---|---|
| [jaeger-trace.png](jaeger-trace.png) | Captura real del timeline de Jaeger: dos servicios, 13 spans, salto HTTP y operación `INSERT credits`. |
| [trace.json](trace.json) | Respuesta del backend Jaeger con relaciones entre spans y atributos `db.system=postgresql`; permite examinar la traza sin depender de la captura. |
| [validation.json](validation.json) | Comprobaciones aprobadas de traza común A/B y presencia de un span PostgreSQL. |

## Métricas y dashboard Grafana

| Evidencia | Qué demuestra |
|---|---|
| [grafana-dashboard.png](grafana-dashboard.png) | Captura real de seis paneles: latencia, errores HTTP, tráfico, disponibilidad/éxito, CPU de servicios y errores del Collector. Refleja la versión capturada, no necesariamente cambios posteriores del dashboard. |
| [dashboard-queries.json](dashboard-queries.json) | 21 consultas exitosas a Prometheus, incluidas las de los seis paneles, CPU del Collector y métricas SDK de memoria y duración HTTP. |
| [targets.json](targets.json) | Cuatro targets con health `up`: A, B, métricas internas del Collector y exporter de métricas OTel. `up` acredita scrape, no disponibilidad completa del negocio. |

Las latencias de Prometheus son estimaciones por histogramas y ventanas; las de k6 se calculan sobre sus observaciones HTTP. Una curva o consulta exitosa no demuestra por sí sola cumplimiento de todos los objetivos de latencia.

## Logs correlacionados con trace_id

| Evidencia | Qué demuestra |
|---|---|
| [logs.json](logs.json) | Registros reales `credit.remote.success` de A y `credit.persisted` de B con el mismo trace_id y sus span_id, recuperados de Loki. |
| [grafana-logs.png](grafana-logs.png) | Captura de Grafana Explore/Loki filtrando por el trace_id de integración, con dos registros visibles. |
| [reference/correlation-runtime.json](reference/correlation-runtime.json) | Plantillas de enlaces logs→trazas y trazas→logs conservadas en la configuración efectiva de Grafana, LogQL resuelto y registros de ambos servicios. También registra que los hashes de la API coinciden con la imagen en ejecución. |

La correlación Grafana–Jaeger–Loki quedó validada mediante provisioning y consultas reales a los backends. Esta evidencia no acredita navegación visual automatizada de exemplars ni asigna un trace_id a cada muestra de métricas agregadas.

## Pruebas automatizadas y de integración

| Evidencia | Qué demuestra |
|---|---|
| [tests.txt](tests.txt) | Suite de 10 pruebas aprobadas en Docker y dos advertencias de deprecación conservadas. |
| [validation.json](validation.json) | 13 comprobaciones de salud, CRUD, 404/422, persistencia tras reiniciar B, trazas A/B/SQL, logs correlacionados, targets y seis paneles. |
| [failure.json](failure.json) | Respuesta controlada 503 de A al no estar disponible B, con mensaje `Credit storage unavailable` y trace_id. Es una prueba funcional de fallo. |
| [reference/k6-scenarios.json](reference/k6-scenarios.json) | Resumen de los escenarios cortos, carga, duración y códigos de salida: normal 99; errores y pico 0. |
| [reference/k6-normal.json](reference/k6-normal.json) | Normal con 10 VUs/20 s: comprobaciones funcionales aprobadas y cero respuestas inesperadas; p99 1241,05 ms incumple el umbral menor de 1000 ms y explica exit 99. p95 sí cumple su umbral. |
| [reference/k6-errors.json](reference/k6-errors.json) | Errores con 10 VUs/20 s: comprobaciones aprobadas, cero respuestas inesperadas y cumplimiento de los umbrales definidos. Los 404/422 intencionales se trataron como esperados. |
| [reference/k6-spike.json](reference/k6-spike.json) | Pico 10→20→10 VUs/30 s: comprobaciones aprobadas, cero respuestas inesperadas y cumplimiento de sus umbrales definidos. |

Errores y pico no imponían un umbral p99. Estas ejecuciones cortas validan escenarios y no sustituyen el benchmark de cinco minutos ni aportan una conclusión estadística de rendimiento.

## Benchmark con y sin OpenTelemetry

### Pareja final

| Evidencia | Qué demuestra |
|---|---|
| [benchmark.json](benchmark.json) | Consolidado de p99, solicitudes, errores y CPU/memoria por servicio; diferencias con/sin SDK y condiciones de ejecución. |
| [without-otel.json](without-otel.json) | Resumen HTTP k6 sin SDK activo: 24784 solicitudes, p99 680,39 ms, comprobaciones aprobadas y tasa de fallo 0. |
| [with-otel.json](with-otel.json) | Resumen HTTP k6 con SDK activo: 16396 solicitudes, p99 2026,96 ms, comprobaciones aprobadas y tasa de fallo 0. |
| [without-otel-resources.csv](without-otel-resources.csv) | 198 muestras timestamp/servicio/CPU/memoria del modo sin SDK, distribuidas entre A, B y Collector. |
| [with-otel-resources.csv](with-otel-resources.csv) | 201 muestras equivalentes del modo con SDK para revisar los promedios y su comparación. |
| [reference/slo-assessment.json](reference/slo-assessment.json) | Evaluación retrospectiva del benchmark guardado: con SDK no se cumplieron los objetivos de referencia p95, p99 ni overhead CPU menor de 5%; funcionalidad y tasa de errores sí cumplieron. No es una nueva ejecución. |

La pareja final usó 50 VUs y cinco minutos por modo, con warm-up de 20 s y límites de 1 CPU/512 MiB por aplicación. A+B suman CPU media 143,74% sin SDK y 165,91% con SDK; memoria 173,25 y 199,03 MiB. El Collector se informa aparte. CPU es porcentaje de un core, no del host completo. En baseline continúan `/metrics`, logs stdout y dependencias instaladas; el Collector permanece encendido.

Se conserva una sola pareja final, ordenada sin→con, con crédito compartido y otros contenedores locales activos. No demuestra significancia estadística ni overhead universal. Todos los valores y archivos originales permanecen sin modificar.

### Pareja exploratoria: conservar sin confundir con el resultado final

| Evidencia | Qué demuestra |
|---|---|
| [exploratory/LIMITACIONES.md](exploratory/LIMITACIONES.md) | Advierte que esta ejecución coincidió con descarga y validación Terraform; no atribuir sus diferencias exclusivamente al SDK. |
| [exploratory/benchmark.json](exploratory/benchmark.json) | Consolidado del primer par, mantenido por transparencia y separado del benchmark final. |
| [exploratory/without-otel.json](exploratory/without-otel.json) | Resumen HTTP del baseline exploratorio. |
| [exploratory/with-otel.json](exploratory/with-otel.json) | Resumen HTTP del modo instrumentado exploratorio. |
| [exploratory/without-otel-resources.csv](exploratory/without-otel-resources.csv) | Muestras de recursos del baseline exploratorio. |
| [exploratory/with-otel-resources.csv](exploratory/with-otel-resources.csv) | Muestras de recursos del modo instrumentado exploratorio. |

## Validación de Terraform AWS y GCP

| Evidencia | Qué demuestra |
|---|---|
| [terraform-aws-init.txt](terraform-aws-init.txt) | Inicialización exitosa de Terraform y providers de AWS. No acredita creación de recursos. |
| [terraform-aws-validate.json](terraform-aws-validate.json) | Validación final AWS con `valid=true`, cero errores y cero advertencias. |
| [terraform-gcp-init.txt](terraform-gcp-init.txt) | Inicialización exitosa de Terraform y providers Google/random. No acredita creación de recursos. |
| [terraform-gcp-validate.json](terraform-gcp-validate.json) | Validación final GCP con `valid=true`, cero errores y cero advertencias. |
| [errors/terraform-aws-rules.json](errors/terraform-aws-rules.json) | Fallo anterior de validación AWS con tres errores de tipos en reglas/rutas. Se conserva como historial; no sustituye el resultado final aprobado. |

Estas evidencias validan esquema y expresiones localmente. No prueban cuotas, permisos efectivos, costos definitivos, arranque remoto ni Collector desplegado en AWS ECS Fargate o Google Cloud Run. Los despliegues permanecen pendientes de autorización.

### Preparación de imágenes y configuraciones cloud, probada localmente

| Evidencia | Qué demuestra |
|---|---|
| [cloud-image-builds.json](cloud-image-builds.json) | Tags e IDs de cinco imágenes auxiliares construidas en Docker local, sin publicación en registries. |
| [cloud-config-validation.json](cloud-config-validation.json) | Validación de configuraciones Collector, Prometheus y Loki con exit 0. |
| [cloud-prometheus-config.txt](cloud-prometheus-config.txt) | Salida textual de validación de sintaxis de Prometheus. |
| [cloud-loki-config.txt](cloud-loki-config.txt) | Mensaje `config is valid` de Loki, junto con la presentación de stderr como NativeCommandError de PowerShell. Se conserva ese detalle; el resultado consolidado exitoso está en cloud-config-validation.json. |
| [cloud-bundle-local.json](cloud-bundle-local.json) | Prueba Docker del bundle destinado a cloud: traza de dos servicios, cuatro targets up y seis paneles. Declara expresamente que es local, no un despliegue cloud. |

## Capturas, integridad y referencia docente

| Evidencia | Qué demuestra |
|---|---|
| [screenshots.json](screenshots.json) | URLs locales y texto visible registrados para las tres capturas reales; no representa una consulta remota actual. |
| [SHA256SUMS.txt](SHA256SUMS.txt) | Manifiesto histórico de hashes. En la revisión de esta carpeta coincidieron 48 archivos listados; dashboard-queries.json no coincide con su hash guardado. No se actualizó el manifiesto y no incluye este índice. Las entradas externas a esta carpeta no se verificaron. |
| [reference/zip-inventory.json](reference/zip-inventory.json) | Inventario de 51 entradas y hash del ZIP docente leído sin extracción ni modificación. La ruta absoluta registrada pertenece al workspace de esa revisión; el ZIP no se duplica aquí. |

## Evidencias faltantes y límites de publicación

- Las siete categorías solicitadas tienen evidencia local. No se encontró ningún archivo faltante entre los enlaces de este índice ni entre las entradas del manifiesto que apuntan dentro de esta carpeta.
- No hay evidencias de despliegues reales ni benchmarks en AWS/GCP: siguen pendientes de autorización.
- No existe un diagrama independiente de arquitectura en esta carpeta; la topología se respalda con el snapshot de servicios, la traza y las comprobaciones de integración.
- No se acredita navegación automatizada de exemplars ni una serie de múltiples parejas de benchmark para incertidumbre estadística.
- El manifiesto SHA256 necesita conciliarse con dashboard-queries.json si se exige integridad de la versión final; se conservó intacto como evidencia histórica.
- Se revisaron 60 archivos existentes: 27 JSON, nueve TXT, cuatro CSV, tres PNG, 15 logs y un documento de limitaciones, además del marcador .gitkeep. Los 15 archivos .log existen localmente pero están excluidos por las reglas actuales de Git; este índice enlaza los JSON/CSV y demás evidencias conservables en GitHub, sin enlaces a logs que quedarían ausentes al publicar. No se cambiaron las reglas de Git.

La revisión fue documental. Solo se creó este README: no se movieron, duplicaron ni modificaron las evidencias; no se ejecutaron pruebas, benchmarks, commit, push o despliegues.
