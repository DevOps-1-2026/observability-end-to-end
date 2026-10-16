# Observabilidad end-to-end con OpenTelemetry

Laboratorio de observabilidad de la Maestría en Arquitectura de Software: una API de créditos en FastAPI con dos microservicios, PostgreSQL y trazas, métricas y logs correlacionados. La implementación está validada localmente. En AWS se prepararon recursos en Ohio (`us-east-2`) y se publicaron las imágenes de la API y del Collector; no se confirmó un despliegue en ECS Fargate ni la recepción de las tres señales. Google Cloud conserva una propuesta Terraform sin despliegue real.

## Entrega del laboratorio

1. [Informe técnico PDF](docs/INFORME_LAB_OTEL.pdf) · [versión editable DOCX](docs/INFORME_LAB_OTEL.docx).
2. [Índice de evidencias locales](docs/evidence/README.md): pruebas, trazas, logs, capturas y benchmark.
3. [Implementación inicial en AWS y capturas originales](docs/IMPLEMENTACION_INICIAL_AWS.md).
4. Código y configuraciones: [aplicación](app/), [infraestructura AWS](infra/aws/), [infraestructura GCP](infra/gcp/), [imágenes y configuración cloud](infra/images/), [OpenTelemetry local](otel/) y [Docker Compose](compose.otel.yml).

El informe distingue resultados locales, recursos preparados y validaciones pendientes. Su [versión textual](docs/ENTREGA_LAB_OTEL.md) facilita la lectura en GitHub; la Figura 1 usa la [imagen actualizada del equipo](docs/ARQUITECTURA_OTEL.png) en PDF y DOCX.

## Autores

- Camilo José Mora Rodríguez
- Danny Tatiana Morales Jiménez
- Juan Daniel Valderrama Pérez

## Arquitectura y herramientas

```text
Cliente → Service A (FastAPI) → HTTP → Service B (FastAPI) → PostgreSQL
                 │                           │
                 └──── OpenTelemetry SDK ────┘
                                │ OTLP
                       OpenTelemetry Collector
                         ├─ trazas → Jaeger
                         ├─ métricas → Prometheus
                         └─ logs → Loki

Grafana consulta Jaeger, Prometheus y Loki. k6 genera carga sobre Service A.
```

Service A expone los endpoints de créditos, `/health`, `/metrics` y la documentación `/docs`. Service B ejecuta las operaciones de persistencia mediante SQLAlchemy y psycopg. PostgreSQL conserva los créditos en un volumen. El contexto de traza W3C se propaga entre A, B y las consultas a la base de datos.

| Herramienta | Función en el laboratorio |
|---|---|
| OpenTelemetry SDK | Instrumentación automática de FastAPI, httpx y SQLAlchemy; spans personalizados, métricas y logs de negocio |
| OpenTelemetry Collector | Recibe OTLP, procesa las tres señales y las exporta a sus backends |
| Jaeger | Consulta de trazas distribuidas A → B → PostgreSQL |
| Prometheus | Almacena métricas del SDK y obtiene scrapes de `/metrics` y del Collector |
| Grafana | Dashboard de seis paneles y consultas correlacionadas a trazas, métricas y logs |
| Loki | Almacena logs enviados por OTLP con `trace_id` y `span_id` |
| k6 | Escenarios normal, errores y pico; carga de comparación con y sin SDK |

Las configuraciones están en [otel/](otel/), el Collector en [otel/collector.yaml](otel/collector.yaml) y los scripts de carga en [load.js](otel/k6/load.js) y [scenarios.js](otel/k6/scenarios.js).

## Ejecución local

Requisitos: Docker Desktop iniciado con contenedores Linux, Docker Compose y PowerShell. Ejecutar los comandos desde la raíz de este repositorio. Python 3 solo se necesita para los scripts de validación descritos en la guía.

### Configurar el entorno

[.env.example](.env.example) contiene los puertos locales y contraseñas de demostración. Compose también tiene valores predeterminados, por lo que copiarlo es opcional. Para crear `.env` sin sobrescribir uno existente:

```powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Editar `.env` si es necesario y mantener `OTEL_ENABLED=true` para observar las tres señales. Los valores predeterminados son `API_PORT=18000`, `JAEGER_PORT=16686`, `PROMETHEUS_PORT=19090` y `GRAFANA_PORT=13000`. Las contraseñas de ejemplo son exclusivamente para uso local. Si ya existe un volumen PostgreSQL, cambiar `POSTGRES_PASSWORD` no cambia automáticamente la contraseña almacenada en la base de datos. No compartir el archivo `.env` ni usar datos reales de clientes.

### Validar e iniciar

Usar [compose.otel.yml](compose.otel.yml) para ejecutar este laboratorio:

```powershell
docker compose -f compose.otel.yml config --quiet
docker compose -f compose.otel.yml up -d --build --wait
docker compose -f compose.otel.yml ps
```

La validación de configuración se comprobó con Docker Compose v5.1.0. El arranque y las pruebas locales están documentados en las evidencias existentes; actualizar este README no ejecutó nuevos contenedores ni pruebas de carga. El arranque descarga imágenes y construye la imagen de la API. k6 pertenece al perfil `load` y no se ejecuta con el arranque habitual.

| Interfaz | Dirección predeterminada |
|---|---|
| API y Swagger | http://localhost:18000/docs |
| Salud de Service A | http://localhost:18000/health |
| Jaeger | http://localhost:16686 |
| Prometheus | http://localhost:19090 |
| Grafana | http://localhost:13000 |

Grafana usa el usuario `lab` y la contraseña configurada en `GRAFANA_PASSWORD`, por defecto `local-lab-only`. Loki se consulta desde Grafana Explore. Service B y PostgreSQL permanecen dentro de la red Compose; las interfaces publicadas escuchan en `127.0.0.1`. Si se cambian los puertos en `.env`, ajustar las direcciones de la tabla. OTLP está publicado en `127.0.0.1:14317` (gRPC) y `127.0.0.1:14318` (HTTP).

### Detener y volver a iniciar

```powershell
docker compose -f compose.otel.yml stop
```

`stop` conserva los contenedores y los volúmenes de PostgreSQL, Prometheus y Loki. Para volver a iniciar:

```powershell
docker compose -f compose.otel.yml up -d --wait
```

Jaeger mantiene las trazas en memoria y las pierde al reiniciar su proceso. Conservar las evidencias necesarias antes de detenerlo. La [guía local](docs/GUIA_LOCAL.md) incluye los procedimientos de validación y recuperación.

## Resultados y documentación de entrega

Las evidencias guardadas registran 10/10 pruebas y 13/13 comprobaciones de integración. La correlación Grafana–Jaeger–Loki quedó validada mediante la configuración efectiva y consultas a los backends. Los escenarios k6 de errores y pico cumplieron sus umbrales. Normal terminó con exit 99 porque p99 fue 1241,05 ms frente al umbral menor de 1000 ms, aunque sus comprobaciones funcionales pasaron.

El benchmark con y sin SDK conserva sus resultados originales: 50 VUs y cinco minutos por modo. Las validaciones cortas de escenarios no reemplazan ese benchmark. No se ejecutaron nuevas cargas ni se modificaron resultados o evidencias para esta actualización.

- [GUIA_LOCAL.md](docs/GUIA_LOCAL.md): requisitos, ejecución y procedimientos locales.
- [ESTADO_FINAL.md](docs/ESTADO_FINAL.md): resultados comprobados, benchmark, limitaciones y requisitos pendientes.
- [INFORME_LAB_OTEL.pdf](docs/INFORME_LAB_OTEL.pdf): informe final de 12 páginas, con formato APA 7, con portada estudiantil.
- [NUBES_COSTOS_Y_ELIMINACION.md](docs/NUBES_COSTOS_Y_ELIMINACION.md): recursos previstos, costos orientativos y eliminación.
- [Evidencias reales](docs/evidence/): pruebas, consultas, capturas y mediciones conservadas.

## AWS y Google Cloud: avances y pendientes

| Plataforma | Avance documentado | Pendiente |
|---|---|---|
| AWS, Ohio (`us-east-2`) | Seis repositorios ECR creados, imágenes API y Collector publicadas, grupo y flujo CloudWatch Logs con retención de siete días; diez pruebas aprobadas en CloudShell | Confirmar servicios activos y validar métricas personalizadas, logs y trazas. El inicio del Collector fuera de ECS quedó bloqueado por ausencia de credenciales SigV4 |
| Google Cloud | [Propuesta Terraform](infra/gcp/) y validaciones locales de esquema e imágenes | Publicar imágenes, desplegar recursos y comprobar aplicación y telemetría en la nube |

La [documentación AWS](docs/IMPLEMENTACION_INICIAL_AWS.md) conserva las capturas y el alcance de cada comprobación. Publicar una imagen en ECR no demuestra un servicio funcionando en ECS Fargate. Las pruebas en CloudShell tampoco prueban el flujo de telemetría. No se confirmó recepción de las tres señales en CloudWatch/X-Ray y no se ejecutó un despliegue en GCP.

La [propuesta Terraform AWS](infra/aws/) y el bundle probado en Docker local son artefactos de preparación; no certifican aprovisionamiento remoto. La preparación inicial AWS documentada usa exportación prevista hacia servicios AWS, mientras el bundle anterior tiene backends propios. No se consideran una única implementación validada.

Antes de cualquier trabajo remoto adicional deben revisarse cuenta, región, permisos, presupuesto, duración y eliminación. La [guía de costos y eliminación](docs/NUBES_COSTOS_Y_ELIMINACION.md) describe la propuesta anterior y sus límites. Esta actualización documental no ejecutó recursos en ninguna nube ni realizó commit o push.
