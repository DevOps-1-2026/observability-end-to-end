# Observabilidad end-to-end con OpenTelemetry

Laboratorio de observabilidad de la Maestría en Arquitectura de Software: una API de créditos en FastAPI con dos microservicios, PostgreSQL y trazas, métricas y logs correlacionados. La implementación está validada localmente; la infraestructura de AWS y Google Cloud está preparada y sus despliegues siguen pendientes de autorización.

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
- [INFORME_LAB_OTEL.pdf](docs/INFORME_LAB_OTEL.pdf): informe de entrega de seis páginas.
- [NUBES_COSTOS_Y_ELIMINACION.md](docs/NUBES_COSTOS_Y_ELIMINACION.md): recursos previstos, costos orientativos y eliminación.
- [Evidencias reales](docs/evidence/): pruebas, consultas, capturas y mediciones conservadas.

## AWS y Google Cloud: preparado y pendiente

| Plataforma | Infraestructura preparada | Despliegue pendiente |
|---|---|---|
| AWS ECS Fargate | [infra/aws/](infra/aws/): tarea con microservicios y observabilidad, RDS PostgreSQL, ECR, red, IAM, logs y secretos | Revisión del plan y costos, autorización, publicación de imágenes y despliegue real |
| Google Cloud Run | [infra/gcp/](infra/gcp/): servicio con microservicios y observabilidad, Cloud SQL PostgreSQL, Artifact Registry, IAM y secretos | Revisión del plan y costos, autorización, publicación de imágenes y despliegue real |

Terraform pasó validación local de esquema; las imágenes y el bundle se probaron en Docker local. Esto no acredita recursos desplegados: no se ejecutaron planes/applies contra cuentas ni se publicaron imágenes. Los microservicios están agrupados en una tarea o instancia para la demostración; la equivalencia con la rúbrica y el escalado independiente siguen sujetos a revisión.

Los despliegues de ambas nubes permanecen pendientes de autorización explícita. Antes de crear recursos se deben acordar servicios, región, presupuesto, duración y plan de eliminación. Las cuentas gratuitas no garantizan costo cero; cómputo, bases de datos, almacenamiento, logs y red pueden consumir presupuesto. Consultar [costos y eliminación](docs/NUBES_COSTOS_Y_ELIMINACION.md) antes de aprobar cualquier acción remota.
