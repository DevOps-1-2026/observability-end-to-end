# Estado final del laboratorio OpenTelemetry

Consolidación documental: 15 de octubre de 2026, America/Bogota. Los resultados corresponden a las evidencias existentes; no se ejecutaron nuevas pruebas ni recursos cloud durante esta revisión.

## Entrega

- [Informe final PDF](INFORME_LAB_OTEL.pdf), 12 páginas con formato APA 7, con portada estudiantil.
- [Versión editable DOCX](INFORME_LAB_OTEL.docx), usada para exportar el mismo contenido y formato a PDF.
- [Versión textual del informe](ENTREGA_LAB_OTEL.md).
- [Índice de evidencias locales](evidence/README.md).
- [Implementación inicial AWS y capturas originales](IMPLEMENTACION_INICIAL_AWS.md).

La Figura 1 fue reemplazada por la [imagen actualizada proporcionada por el equipo](ARQUITECTURA_OTEL.png). Su nota distingue recursos AWS preparados y despliegue ECS propuesto; no acredita recepción de telemetría.

## Resultados locales comprobados

La cadena Service A → HTTP → Service B → PostgreSQL fue validada con Docker Compose. La suite registra 10/10 pruebas aprobadas y dos advertencias de deprecación en [tests.txt](evidence/tests.txt); [validation.json](evidence/validation.json) registra 13/13 comprobaciones de integración, incluida persistencia después de reiniciar B, traza A/B/PostgreSQL, logs correlacionados, cuatro targets Prometheus activos y seis paneles Grafana.

[Failure.json](evidence/failure.json) registra HTTP 503 ante la interrupción de B. La correlación usa el trace_id `868d7e4a569d404cb1dcfa718703ab90`; [correlation-runtime.json](evidence/reference/correlation-runtime.json) conserva la configuración efectiva y las consultas a los backends. No se acredita navegación visual automatizada de exemplars.

Los escenarios cortos k6 de errores y pico cumplieron sus umbrales. Normal tuvo comprobaciones funcionales aprobadas, pero exit 99: p99 1241,05 ms incumplió el umbral menor de 1000 ms. Ver [k6-scenarios.json](evidence/reference/k6-scenarios.json).

## Benchmark final

50 usuarios virtuales, cinco minutos por modo y calentamiento de veinte segundos. Una pareja final, orden sin→con, carga de lectura/actualización sobre un crédito compartido, límite de 1 CPU/512 MiB por aplicación. No se generaliza a producción.

| Indicador | Sin OTel | Con OTel |
|---|---:|---:|
| Latencia p99 | 680,39 ms | 2.026,96 ms |
| CPU media A+B | 143,74 % | 165,91 % |
| Memoria media A+B | 173,25 MiB | 199,03 MiB |
| Solicitudes procesadas | 24.784 | 16.396 |
| Errores HTTP | 0 % | 0 % |

El incremento relativo fue 197,91 % en p99 y 15,42 % en CPU; memoria adicional 25,78 MiB. CPU es porcentaje de un core, sumado entre A y B; el Collector se informa aparte. El modo sin SDK conserva /metrics, stdout y dependencias instaladas. La pareja exploratoria se conserva separada. Archivos y límites: [benchmark.json](evidence/benchmark.json) y el [índice](evidence/README.md).

## AWS: preparación inicial documentada

En Ohio (`us-east-2`) se crearon seis repositorios ECR y se publicaron imágenes de API y Collector con etiqueta `aws`. Se creó el grupo `/ecs/otel-credit-lab/otel-logs`, flujo `otel`, con retención de siete días. CloudShell registró diez pruebas aprobadas, una advertencia y aproximadamente 0,75 segundos.

La configuración del Collector contempla OTLP y exportación prevista a X-Ray, CloudWatch Metrics y CloudWatch Logs. Su inicio fuera de ECS quedó bloqueado por ausencia de credenciales para SigV4. No se confirmaron métricas personalizadas, logs de aplicación ni trazas recibidas. No hay evidencia suficiente de aplicación o Collector funcionando en ECS Fargate. Publicar imágenes y preparar destinos no equivale a validar servicios activos.

La [documentación AWS](IMPLEMENTACION_INICIAL_AWS.md) conserva las siete capturas originales y distingue cada alcance. La propuesta [Terraform AWS](../infra/aws/) y el bundle probado en Docker local no certifican los recursos remotos ni su operación.

## Google Cloud: propuesta sin despliegue

Se preparó [Terraform GCP](../infra/gcp/) y se validó localmente con `valid=true`; también existen pruebas Docker locales del bundle destinado a nube. No se efectuó un despliegue GCP ni se validó telemetría allí. Quedan pendientes publicación de imágenes, aprovisionamiento, arranque y comprobaciones funcionales y de señales.

## Límites y pendientes

- AWS: revisar credenciales, permisos y compatibilidad de destinos; comprobar servicios activos y recepción de cada señal.
- GCP: desplegar y repetir validaciones con recursos reales, después de la aprobación correspondiente.
- Rendimiento: repetir pares y alternar orden para estimar variabilidad; la pareja local no da significancia estadística.
- Integridad histórica: el índice conserva la discrepancia previamente documentada de `dashboard-queries.json` frente al manifiesto SHA256. No se alteró el manifiesto ni la evidencia para ocultarla.
- Publicación: el PDF final ya no se excluye de Git. Los archivos están preparados localmente; no se ejecutaron git add, commit ni push. Los enlaces GitHub a archivos nuevos o renombrados estarán disponibles cuando el equipo publique los cambios.

La [guía local](GUIA_LOCAL.md) conserva los procedimientos de reproducción y [costos y eliminación](NUBES_COSTOS_Y_ELIMINACION.md) describe la propuesta histórica. Sus estimaciones no constituyen una cotización vigente. No se modificó Python, Terraform, Docker, Compose ni configuración OpenTelemetry; tampoco capturas, resultados o el PDF original.
