import json, html, textwrap
from pathlib import Path
from datetime import datetime, timezone, timedelta
root=Path.cwd();out=root/'docs';e=out/'evidence'
b=json.loads((e/'benchmark.json').read_text(encoding='utf-8'));v=json.loads((e/'validation.json').read_text(encoding='utf-8'))
a=b['without-otel'];o=b['with-otel'];d=b['comparison']
validation={cloud:json.loads((e/f'terraform-{cloud}-validate.json').read_text(encoding='utf-8-sig'))['valid'] for cloud in ['aws','gcp']}
when=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d %H:%M America/Bogota')
apps=lambda r,key:sum(r['resources'][s][key] for s in ['service-a','service-b'])
bench=f"""| Medición | Sin SDK OTel | Con SDK OTel | Diferencia |
|---|---:|---:|---:|
| p99 HTTP k6 (ms) | {a['p99_ms']:.2f} | {o['p99_ms']:.2f} | {d['p99_ms']['absolute']:+.2f} ms ({d['p99_ms']['percent']:+.2f}%) |
| CPU A+B (% de un core, media) | {apps(a,'cpu_mean_percent'):.2f} | {apps(o,'cpu_mean_percent'):.2f} | {d['apps_cpu_percent']['absolute']:+.2f} puntos ({d['apps_cpu_percent']['percent']:+.2f}%) |
| Memoria A+B (MiB, media) | {apps(a,'memory_mean_mib'):.2f} | {apps(o,'memory_mean_mib'):.2f} | {d['apps_memory_mib']['absolute']:+.2f} MiB ({d['apps_memory_mib']['percent']:+.2f}%) |
| Requests | {a['requests']} | {o['requests']} | Carga de VUs constante, throughput variable |
| Tasa errores HTTP | {a['failed_rate']:.4%} | {o['failed_rate']:.4%} | Umbral k6: menos de 1% |
| CPU Collector (% de un core) | {a['resources']['collector']['cpu_mean_percent']:.2f} | {o['resources']['collector']['cpu_mean_percent']:.2f} | Separado del overhead A+B |
| Memoria Collector (MiB) | {a['resources']['collector']['memory_mean_mib']:.2f} | {o['resources']['collector']['memory_mean_mib']:.2f} | Separada de memoria A+B |"""
state=f"""# Estado final del laboratorio OpenTelemetry

Consolidado: {when}. Implementado y validado localmente. Infraestructura AWS/GCP preparada y validada por Terraform; **ningún recurso cloud desplegado**, ninguna imagen publicada y ningún terraform plan/apply contra cuentas ejecutado.

## Resultados comprobados

- Pruebas: 10/10 (ocho originales y dos nuevas), con advertencias de deprecación de TestClient. Evidencia: tests.txt.
- Integración: {len(v['checks'])}/{len(v['checks'])} comprobaciones; CRUD, 404/422, persistencia al reiniciar B, trace A/B/PostgreSQL, logs Loki vía Grafana, targets Prometheus y seis paneles. Evidencia: validation.json, trace.json, logs.json, targets.json y dashboard-queries.json.
- Imágenes cloud: cinco construidas y bundle de ocho contenedores probado en Docker local (CRUD, traza, gateway, targets y Grafana). Evidencias cloud-image-builds.json/cloud-bundle-local.json; contenedores de prueba detenidos. No es despliegue cloud.
- Capturas reales: jaeger-trace.png, grafana-dashboard.png y grafana-logs.png, inspeccionadas visualmente.
- Falla controlada: B detenido, A devuelve 503 y B se restaura; failure.json.
- Benchmark: 50 VUs, cinco minutos por modo y warm-up 20s; datos sintéticos compartidos, 1 CPU/512 MiB por app. Dos parejas ejecutadas: la exploratoria se conserva en evidence/exploratory y la pareja final se ejecutó sin instalaciones/builds/validaciones de infraestructura simultáneos.
- Terraform AWS: valid={validation['aws']}; GCP: valid={validation['gcp']}. init sin backend y validate; evidencia terraform-*-validate.json e init.txt. Validar esquema no demuestra despliegue.

## Benchmark final

{bench}

Mediciones de Docker stats promediadas por servicio y sumadas para A/B; ver CSV para cantidad exacta de muestras. CPU % de un core no es porcentaje del host completo. Con/sin mantiene /metrics, logs stdout y dependencias SDK importadas: compara instrumentación/exportación SDK activa frente a desactivada. Collector encendido en ambos modos, inactivo respecto de aplicaciones en baseline. Se restauró OTEL_ENABLED=true al terminar.

Una pareja final, orden sin→con y workload GET/PUT sobre el mismo crédito. No es un intervalo de confianza ni demuestra overhead general para todas las cargas. El primer par coincidió con preparación de Terraform y quedó etiquetado exploratorio. Los valores pueden variar por carga del host Docker/Windows, caché y orden. Todos los PUT comparten fila y pueden crear contención; no representa todas las cargas de créditos. No se inventan resultados cloud ni promesas de latencia.

## Matriz de requisitos

| Requisito | Implementado/probado | Evidencia/archivo | Pendiente, riesgo y siguiente paso |
|---|---|---|---|
| Contratos de créditos y /metrics | Sí, tests y CRUD real | app/main.py, service.py, tests.txt | Memoria solo fallback; Compose usa B |
| Dos microservicios + PostgreSQL | Sí, HTTP A→B y DB persistente | app/storage.py, compose.otel.yml, validation.json | No migración automática del diccionario histórico |
| SDK auto + spans propios | Sí, FastAPI/httpx/SQLAlchemy y credit.* | app/telemetry.py, trace.json | Mantener versiones compatibles |
| TraceContext W3C | Sí, trace_id común {v['trace_id']} | trace.json y logs.json | Repetir en cada nube autorizada |
| Tres señales | Sí, OTLP trazas/métricas/logs | Collector, Loki, SDK y targets | Logs uvicorn no estructurados ni exportados como negocio |
| Collector completo/versionado | Sí, local; grpc/http y 3 pipelines | otel/collector.yaml, collector.txt | Despliegue en ambas nubes pendiente de autorización |
| Jaeger, Prometheus, Grafana, Loki | Sí, APIs y provisioning | targets.json, validation.json | Datos de Jaeger en memoria; exportar antes de reinicio |
| Dashboard seis paneles | Sí, provisioning y queries ejecutadas | dashboard.json, dashboard-queries.json | Cero eventos Collector puede no crear serie; fallback cero documentado |
| Correlación logs↔trazas | Sí, mismo ID en ambos servicios | logs.json, trace.json | Navegación visual del enlace y exemplars no verificadas automáticamente |
| Benchmark p99/CPU/memoria | Sí, 2 pares, final comparable en setup | benchmark.json, summaries, CSV | Repetir varias veces y alternar orden para estadística |
| Falla controlada | Sí, A 503 cuando B no disponible | failure.json | No es un benchmark de fallas de cinco minutos |
| IaC AWS/GCP | Sí, Terraform validate local | infra/aws y infra/gcp, lockfiles | Cuotas/IAM/costos/imágenes/arranque remoto sin probar |
| Collector desplegado AWS/GCP | No | docs/NUBES_COSTOS_Y_ELIMINACION.md | Obtener autorización del plan antes de desplegar |
| Requisitos de la profesora | Referencia parcial | Skill local | Falta oTelLabs.zip; confirmar bundle vs servicios separados |
| Reporte ≥5 páginas | Generado con evidencias reales | INFORME_LAB_OTEL.pdf y ENTREGA_LAB_OTEL.md | Revisar autores y rúbrica original; capturas reales en evidence |
| Repositorio para entrega | Archivos preparados, sin .git en workspace | README y docs | Inicializar/restaurar Git y publicar solo con autorización |

## Archivos y ejecución

Cambios: app/main.py, app/service.py, requirements.txt, README.md y .gitignore; nuevos app/storage.py, app/telemetry.py, compose.otel.yml, .env.example, .dockerignore, tests/test_remote.py, otel/, scripts/, infra/aws/, infra/gcp/, infra/images/ y docs/. Se conserva Compose anterior, monitoreo anterior, CI/CD, Jenkins y Kubernetes. No se creó rama porque no hay .git.

Puertos locales: API 18000, Jaeger 16686, Prometheus 19090, Grafana 13000, OTLP 14317/14318, todos en loopback. Monitoreo anterior 3000/9090 intacto. Grafana lab/local-lab-only solo local.

Comandos reproducibles: `docker compose -f compose.otel.yml up -d --build --wait`, `python scripts/validate_local.py`, `python scripts/validate_failure.py`, `python scripts/benchmark.py`, `powershell -NoProfile -File scripts/validate_infra.ps1`. Ver GUIA_LOCAL.md para detalles y snapshots disponibles. Detener con `docker compose -f compose.otel.yml stop`; no eliminar volúmenes sin permiso.

Línea base host falló antes de ejecutar tests por falta de prometheus_client. La suite pasó dentro de Docker. Terraform primero tuvo un problema PowerShell con stderr, luego timeout del provider sobre bind mount Windows; se corrigió usando un volumen Linux dedicado. Esos fallos no se ocultan ni se consideran pruebas exitosas. Los errores anteriores están conservados donde corresponde en evidence.

## Nubes: recursos, costos y eliminación

AWS: tarea Fargate 2vCPU/4GiB, RDS 20GiB, VPC/subnets/SG/IPv4, seis ECR, Logs y Secrets/IAM. Fargate ≈US$0.0987/h solo cómputo. Google: Cloud Run 8vCPU/4GiB activo, Cloud SQL 10GiB, registry, secretos, logs/IAM; Cloud Run ≈US$0.5472/h solo cómputo. DB, disco, logs, secretos y transferencias son adicionales; créditos gratuitos sin verificar. Detalle y fuentes: NUBES_COSTOS_Y_ELIMINACION.md.

La eliminación requiere aprobación y plan -destroy; borrar solo imágenes propias si bloquean registries y revisar secretos/snapshots residuales. Bases de datos sin protección de borrado: exportar créditos primero. No se ejecutó eliminación ni despliegue cloud. Siguiente paso remoto: cotejar guía de profesora, elegir duración/presupuesto/región y aprobar un plan concreto.

## Texto para preparar la entrega

> Adjunto docs/ESTADO_FINAL.md, INFORME_LAB_OTEL.pdf, archivos actualizados y docs/evidence. Ayúdame a ajustar el informe a la rúbrica original, incluyendo autores y capturas. Usa solo las pruebas y mediciones guardadas; distingue validación local e IaC preparada de despliegues AWS/GCP todavía no autorizados. No presentes capturas complementarias pendientes ni planes como ejecuciones reales.
"""
(out/'ESTADO_FINAL.md').write_text(state,encoding='utf-8')
# Six substantive sections, explicitly separated for print and PDF.
sections=[
('1. Arquitectura y alcance',f"""El laboratorio adapta una API de créditos de FastAPI a una arquitectura distribuida con dos microservicios. Service A conserva health, creación, listado, consulta por UUID, actualización de estado y métricas. Service B recibe solicitudes HTTP internas y utiliza PostgreSQL mediante SQLAlchemy y psycopg. Los contratos públicos y las pruebas originales permanecen vigentes. El estado inicial es PENDING y los estados válidos son PENDING, APPROVED y REJECTED.

En Docker Compose A resuelve B mediante DNS de servicio y nunca usa localhost para el salto entre contenedores. PostgreSQL emplea un volumen independiente del monitoreo histórico. El modelo relacional registra identificación de la solicitud, campos de entrada y estado, con transacciones para escritura. Un reinicio de B conserva los registros. Para compatibilidad con las pruebas y ejecución histórica sin SERVICE_B_URL, A puede seguir usando un diccionario; ese fallback no representa persistencia y no se usa en el stack del laboratorio.

La topología de observabilidad tiene Collector, Jaeger, Prometheus, Grafana y Loki. Cada proceso FastAPI configura su SDK cuando OTEL_ENABLED=true. El Collector recibe OTLP por HTTP y gRPC, procesa memoria y batches y entrega las tres señales a backends consultables. Prometheus también conserva los scrapes /metrics de la aplicación. Grafana integra las fuentes y seis paneles de observabilidad.

La infraestructura futura AWS/GCP está preparada como Terraform JSON y con imágenes derivadas que incorporan sus configuraciones. Los dos microservicios se empaquetan en una misma tarea o instancia junto con observabilidad, con PostgreSQL administrado externo. Este enfoque es apropiado para una demostración breve pero no permite escalado independiente, alta disponibilidad ni retención durable de señales. La aceptación de ese empaquetado depende de cotejar la guía original de la profesora, que no estuvo disponible en el workspace.

Este documento distingue evidencia local, código preparado y recursos desplegados. No se ejecutaron acciones en cuentas AWS ni Google Cloud. Las cuentas gratuitas mencionadas por la estudiante no se inspeccionaron y no implican costo cero. Los puertos locales nuevos evitan interferir con los contenedores históricos de monitoreo.

Archivos de arquitectura: compose.otel.yml, app/main.py, app/service.py, app/storage.py, app/telemetry.py, otel/ e infra/. Guías de reproducción: GUIA_LOCAL.md y NUBES_COSTOS_Y_ELIMINACION.md. Fecha de consolidación: {when}."""),
('2. Instrumentación y señales',"""La instrumentación automática cubre FastAPI, cliente HTTP httpx y SQLAlchemy. Cada salto crea spans de servidor, cliente y consulta, propagando W3C TraceContext. Los spans personalizados representan creación, lectura, persistencia y actualización de estado. No se agregan documentos o nombres de clientes como atributos de spans ni mensajes de negocio; los datos de carga son sintéticos. Las consultas instrumentadas mantienen parámetros SQL separados.

El SDK configura recursos con service.name y entorno de laboratorio. TracerProvider usa BatchSpanProcessor y exportador OTLP HTTP. MeterProvider emplea un lector periódico con exportación cada cinco segundos. LoggerProvider registra eventos mediante OTLP, además de un handler stdout con formato JSON. Los eventos correlacionados llevan timestamp, nivel, nombre de servicio, trace_id y span_id. Los logs de acceso de uvicorn siguen siendo logs operativos de texto; no se confunden con los registros de negocio exportados.

El Collector versionado aplica memory_limiter antes de resource y batch. El límite de memoria del procesador es 384 MiB, inferior al máximo del contenedor de 512 MiB. OTLP recibe en 4317 y 4318 dentro de la red de laboratorio. Jaeger recibe trazas por OTLP; Prometheus consulta el exporter de métricas en 8889 y las métricas internas de Collector en 8888. Loki ingiere logs mediante su endpoint OTLP nativo y conserva trace_id como metadato estructurado, sin convertir UUID por solicitud en etiqueta de índice.

El dashboard utiliza las métricas históricas para mantener visibilidad durante el baseline sin SDK. Las mediciones SDK no se suman a las métricas equivalentes de /metrics, evitando duplicar el tráfico aparente. El SDK añade CPU acumulada y memoria del proceso; el benchmark usa docker stats por contenedor, una fuente distinta y explícitamente identificada.

OTEL_ENABLED requiere recrear o reiniciar los procesos con la variable cambiada. false desactiva proveedores e instrumentadores, pero los paquetes siguen instalados y /metrics continúa activo. Así se mide el costo de instrumentar y exportar señales sobre el mismo negocio; no se compara una imagen mínima con otra de dependencias diferentes. El Collector permanece encendido en ambos modos.

Las versiones de SDK e instrumentadores pertenecen a la misma familia compatible 1.38.0 y 0.59b0. Collector 0.139.0, Jaeger 1.64.0, Prometheus 3.2.1, Grafana 11.6.0, Loki 3.4.2 y k6 0.57.0 se fijan para reproducibilidad. Las dependencias efectivas se guardan en la evidencia de freeze."""),
('3. Pruebas y correlación',f"""La suite unitaria contiene las ocho pruebas existentes y dos adicionales. Las primeras comprueban salud, métricas, UUID, estado PENDING, listado, consulta, 404, actualización y rechazo de estado inválido. Las nuevas ejercitan el adaptador HTTP y su traducción de fallos de transporte a 503. El resultado dentro de Docker fue diez pruebas exitosas; las advertencias de deprecación de TestClient se conservan en el registro. Antes de modificar, el Python host no pudo colectar la suite por una dependencia ausente, de modo que no se afirmó una línea base exitosa en ese entorno.

La integración real utiliza la API publicada localmente y un traceparent sintético. Comprueba creación, lectura, listado, actualización, 404, validación 422 y persistencia después de reiniciar B. Consulta Jaeger y exige una traza con procesos service-a y service-b y un span identificado como PostgreSQL. Consulta Loki por el proxy autenticado de Grafana y exige registros correlacionados de ambos servicios. Verifica además los targets Prometheus y el dashboard provisionado de seis paneles. El resultado fue {len(v['checks'])} comprobaciones exitosas.

El trace_id registrado en esta consolidación es {v['trace_id']}. El archivo trace.json contiene los spans y procesos reales; logs.json contiene el resultado de Loki; validation.json enumera las aserciones. Esta evidencia es verificable sin depender de una captura de pantalla o una afirmación verbal. Los campos trace_id y span_id en registros OTLP son metadatos estructurados y se correlacionan con la traza del backend.

Las métricas son agregadas: no se afirma que compartan un trace_id por cada muestra. El servicio y la ventana temporal permiten contextualizar un pico de latencia frente a trazas y logs. Se configuró un destino para exemplars y un enlace desde trace_id a Jaeger, pero la navegación visual de exemplars y del enlace no se declaró comprobada automáticamente.

Una prueba adicional detuvo solamente B y comprobó que A devolviera 503 con el mensaje Credit storage unavailable. Un bloque finally restauró B y esperó su salud. No se borraron datos ni se manipularon los contenedores históricos. La evidencia failure.json conserva el código, respuesta y trace_id de esa falla.

Las capturas GUI y la cotejación con oTelLabs.zip siguen siendo trabajo editorial o de validación externa. El workspace carece de .git: los archivos están preparados pero no se creó rama ni se publicó repositorio. Estos pendientes no se convierten en resultados completados."""),
('4. Benchmark y resultados',f"""Se ejecutó carga constante de cincuenta usuarios virtuales durante cinco minutos en cada modo, precedida por veinte segundos de warm-up. Cada iteración consulta un crédito sintético y actualiza su estado. Los modos comparten UUID, volumen, dependencias y límites por aplicación de un core y 512 MiB. El dataset queda acotado para que el listado creciente o la creación continua no distorsionen la comparación. Las métricas HTTP incluyen nombres estables read/update, evitando series por identificador.

Se midió el p99 de duración HTTP mediante k6. Los JSON resumen conservan además distribución, requests y tasa de errores. Las muestras de docker stats registran timestamp UTC, servicio, CPU porcentual y memoria MiB. CPU representa porcentaje de un core; los promedios A y B se suman para estimar el consumo de aplicaciones. El Collector se reporta aparte para no confundir costo de SDK con costo de procesamiento de señales. Las muestras individuales están disponibles en CSV.

Resultado sin SDK: p99 {a['p99_ms']:.2f} ms, {a['requests']} solicitudes y tasa de fallo {a['failed_rate']:.4%}. Resultado con SDK: p99 {o['p99_ms']:.2f} ms, {o['requests']} solicitudes y tasa de fallo {o['failed_rate']:.4%}. Diferencia p99: {d['p99_ms']['absolute']:+.2f} ms, equivalente a {d['p99_ms']['percent']:+.2f}% respecto al baseline.

CPU media A+B: {apps(a,'cpu_mean_percent'):.2f}% sin SDK y {apps(o,'cpu_mean_percent'):.2f}% con SDK. El cambio relativo es {d['apps_cpu_percent']['percent']:+.2f}%. Memoria media A+B: {apps(a,'memory_mean_mib'):.2f} MiB frente a {apps(o,'memory_mean_mib'):.2f} MiB; diferencia {d['apps_memory_mib']['absolute']:+.2f} MiB ({d['apps_memory_mib']['percent']:+.2f}%). Estas cifras no describen CPU del host completo ni memoria RSS de un único proceso.

Se conservó un primer par exploratorio que coincidió con preparación de Terraform. El par final se ejecutó después de terminar instalaciones, builds y validaciones, sin tareas de preparación simultáneas. Los contenedores históricos de monitoreo siguieron activos en ambos modos. El orden fue sin SDK seguido de con SDK; una pareja final no permite calcular intervalos de confianza ni eliminar sesgos de caché y orden. Para estimación estadística se recomienda repetir y alternar orden.

OTEL_ENABLED=true se restauró al finalizar. La prueba controlada de fallo es funcional y no una carga de cinco minutos con fallas. No se reportaron benchmarks cloud. Los resultados son observaciones de este host Windows/Docker y este workload, sin generalizar a producción."""),
('5. Infraestructura, costos y reversión',"""AWS prepara una VPC con una subnet pública para ECS y dos privadas para RDS; security groups restringen el acceso al gateway al IPv4 /32 aprobado de la estudiante y PostgreSQL a la tarea. Una tarea Fargate con dos vCPU y cuatro GiB agrupa ocho contenedores. RDS PostgreSQL administra la persistencia; Secrets Manager entrega la contraseña a B sin incorporarla a la imagen. Se preparan seis ECR, un grupo CloudWatch Logs y roles IAM de ejecución y tarea. No se incluyen NAT Gateway ni ALB.

Google prepara un servicio Cloud Run con ocho contenedores de un vCPU cada uno y memoria total de 4 GiB. CPU siempre asignada y una instancia mínima sostienen Collector y scrapes de fondo. Cloud SQL mantiene PostgreSQL mediante socket de conexión autorizado; Artifact Registry almacena imágenes derivadas. Secret Manager contiene DB y Grafana y la cuenta de servicio recibe permisos limitados de SQL y secretos. El ingreso requiere IAM run.invoker para una identidad concreta; no se asigna allUsers.

Las imágenes auxiliares incorporan la configuración cloud y usan localhost porque los contenedores comparten el namespace de red de una tarea/instancia. El gateway expone API y rutas de interfaces; OTLP y DB quedan fuera del ingreso público. La configuración local utiliza DNS de Compose y no se confunde con esta excepción del empaquetado cloud. La separación por contenedores no aporta escalado independiente: cotejar ese punto con la guía original.

Terraform validate se ejecuta en Docker sin backend y sin credenciales. La validación confirma estructura de recursos y expresiones; no confirma cuotas, permisos efectivos, disponibilidad regional ni arranque remoto. Los providers se fijan mediante lockfiles. Un problema inicial de arranque del provider sobre el bind mount Windows se resolvió con un volumen Linux. No se ejecutaron terraform plan/apply con cuentas.

El costo orientativo de cómputo es US$0.0987/h para Fargate y US$0.5472/h para Cloud Run, antes de RDS/Cloud SQL, discos, secretos, registries, logs, red e impuestos. La cuota o crédito gratuito del usuario no se verificó. Cloud Run con minimum instances=1 y las bases de datos generan costo aunque nadie utilice la API. Consultar las fuentes oficiales y una cotización regional antes de aprobar.

La reversión requiere exportar evidencias y créditos necesarios, aprobar el plan de destroy y borrar únicamente los recursos propios. ECR no fuerza eliminación de imágenes; hay que autorizar su limpieza. El secreto Grafana externo AWS no pertenece al estado y no debe borrarse si era preexistente. Las APIs GCP y el proyecto compartido se conservan. Ambas DB permiten borrado sin protección para demostración: destroy pierde datos. Nada de esto se ejecutó en nube."""),
('6. Conclusiones y entrega',f"""La adaptación local cumple la cadena de dos procesos HTTP y PostgreSQL, mantiene los contratos de créditos y ofrece instrumentación automática y personalizada. Las tres señales llegan a backends consultables: trazas en Jaeger, métricas en Prometheus y logs en Loki. Grafana provisiona fuentes y seis paneles. La evidencia incluye una traza común de A/B/DB y registros correlacionados, pruebas funcionales y mediciones de carga. La conclusión se limita a ejecuciones locales comprobadas.

Las pruebas unitarias se reproducen en la imagen construida con Dockerfile, montando tests en solo lectura. La integración se reproduce con python scripts/validate_local.py. El benchmark se reproduce con python scripts/benchmark.py y tarda más de diez minutos. Terraform se valida mediante scripts/validate_infra.ps1. La documentación conserva comandos para detener el stack con stop y preservar volúmenes, evitando acciones destructivas como down -v o prune.

La entrega consta de código actualizado, compose.otel.yml, configuraciones OTel/backends, dashboard, scripts de prueba, IaC AWS/GCP, lockfiles y carpeta docs/evidence. ESTADO_FINAL.md enumera por requisito implementación, prueba, archivo, pendiente, riesgo y siguiente paso. GUIA_LOCAL.md explica la operación; NUBES_COSTOS_Y_ELIMINACION.md documenta recursos y costos sin desplegarlos. Este informe tiene seis secciones paginadas y no sustituye las evidencias de ejecución.

Pendientes: obtener y revisar oTelLabs.zip y rúbrica original; confirmar si dos microservicios agrupados en una tarea/instancia satisfacen la evaluación; revisar autores y capturas complementarias; restaurar o inicializar Git con autorización de publicación; repetir más pares de carga para incertidumbre estadística; verificar navegación de enlaces y exemplars en la interfaz. Ninguno de estos pendientes se oculta ni se marca como cumplido por tener archivos preparados.

El criterio de Collector desplegado en ambas nubes no está satisfecho. Para cumplirlo se necesita aprobar una propuesta concreta con cuenta/proyecto, región, presupuesto, duración, imágenes y plan Terraform. Después del despliegue autorizado deberán repetirse CRUD, trazas y logs y registrar recursos activos. Las cuentas disponibles no son evidencia de despliegue. El objetivo actual terminó en infraestructura revisable, no en aprovisionamiento remoto.

La seguridad del laboratorio evita secretos versionados y datos personales en telemetría. Los ejemplos locales se publican solo en loopback. La configuración cloud distingue ingreso IAM en GCP y CIDR restringido AWS; AWS sin HTTPS es únicamente una demostración con datos sintéticos. Los estados Terraform que contengan contraseñas deben protegerse y no adjuntarse a la entrega.

Fecha de consolidación: {when}. Evidencias principales: validation.json, trace.json, logs.json, targets.json, failure.json, benchmark.json, summaries/CSV de ambos modos y terraform-*-validate.json. Los valores reportados son los guardados en esos archivos, sin datos inventados ni ejecución cloud supuesta."""),
]
md='# Informe del laboratorio OpenTelemetry\n\n'+'\n\n'.join('## '+title+'\n\n'+body for title,body in sections)
(out/'ENTREGA_LAB_OTEL.md').write_text(md,encoding='utf-8')
html_report='<!doctype html><html lang="es"><meta charset="utf-8"><title>Laboratorio OpenTelemetry</title><style>@page{size:A4;margin:18mm}body{font:11pt Arial;line-height:1.35}section{break-after:page}section:last-child{break-after:auto}h1{font-size:18pt}h2{font-size:15pt}p{text-align:justify}</style><body>'
for title,body in sections:
 html_report+='<section><h1>Laboratorio OpenTelemetry de créditos</h1><h2>'+html.escape(title)+'</h2>'+''.join('<p>'+html.escape(p)+'</p>' for p in body.split('\n\n'))+'</section>'
(out/'INFORME_LAB_OTEL.html').write_text(html_report+'</body></html>',encoding='utf-8')
# Dependency-free PDF with WinAnsi standard fonts; source Markdown/HTML remain editable.
objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>']
page_ids=[]
def literal(s):return s.encode('cp1252',errors='replace').replace(b'\\',b'\\\\').replace(b'(',b'\\(').replace(b')',b'\\)')
for number,(title,body) in enumerate(sections,1):
 lines=[]
 for p in body.split('\n\n'):lines.extend(textwrap.wrap(p,105));lines.append('')
 assert len(lines)<=63,(title,len(lines))
 cmds=[b'BT /F2 16 Tf 40 805 Td ('+literal('Laboratorio OpenTelemetry de créditos')+b') Tj ET',b'BT /F2 12 Tf 40 780 Td ('+literal(title)+b') Tj ET',b'BT /F1 10 Tf 12 TL 40 755 Td']
 for line in lines:cmds.append(b'('+literal(line)+b') Tj T*')
 cmds.append(b'ET');cmds.append(b'BT /F1 9 Tf 40 30 Td ('+literal(f'Implementación local comprobada | Sin despliegues cloud | Página {number}/6')+b') Tj ET')
 content=b'\n'.join(cmds)
 pageid=len(objects)+1;contentid=pageid+1;page_ids.append(pageid)
 objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {contentid} 0 R >>'.encode())
 objects.append(b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream')
objects[1]=b'<< /Type /Pages /Kids ['+b' '.join(f'{id} 0 R'.encode() for id in page_ids)+b'] /Count 6 >>'
pdf=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
for n,obj in enumerate(objects,1):offsets.append(len(pdf));pdf.extend(f'{n} 0 obj\n'.encode()+obj+b'\nendobj\n')
xref=len(pdf);pdf.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
for off in offsets[1:]:pdf.extend(f'{off:010d} 00000 n \n'.encode())
pdf.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode())
(out/'INFORME_LAB_OTEL.pdf').write_bytes(pdf)
print('Estado final, fuente editable e informe PDF de seis páginas generados.')
