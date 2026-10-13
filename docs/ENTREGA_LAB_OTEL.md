# Informe del laboratorio OpenTelemetry

## 1. Arquitectura y alcance

El laboratorio adapta una API de créditos de FastAPI a una arquitectura distribuida con dos microservicios. Service A conserva health, creación, listado, consulta por UUID, actualización de estado y métricas. Service B recibe solicitudes HTTP internas y utiliza PostgreSQL mediante SQLAlchemy y psycopg. Los contratos públicos y las pruebas originales permanecen vigentes. El estado inicial es PENDING y los estados válidos son PENDING, APPROVED y REJECTED.

En Docker Compose A resuelve B mediante DNS de servicio y nunca usa localhost para el salto entre contenedores. PostgreSQL emplea un volumen independiente del monitoreo histórico. El modelo relacional registra identificación de la solicitud, campos de entrada y estado, con transacciones para escritura. Un reinicio de B conserva los registros. Para compatibilidad con las pruebas y ejecución histórica sin SERVICE_B_URL, A puede seguir usando un diccionario; ese fallback no representa persistencia y no se usa en el stack del laboratorio.

La topología de observabilidad tiene Collector, Jaeger, Prometheus, Grafana y Loki. Cada proceso FastAPI configura su SDK cuando OTEL_ENABLED=true. El Collector recibe OTLP por HTTP y gRPC, procesa memoria y batches y entrega las tres señales a backends consultables. Prometheus también conserva los scrapes /metrics de la aplicación. Grafana integra las fuentes y seis paneles de observabilidad.

La infraestructura futura AWS/GCP está preparada como Terraform JSON y con imágenes derivadas que incorporan sus configuraciones. Los dos microservicios se empaquetan en una misma tarea o instancia junto con observabilidad, con PostgreSQL administrado externo. Este enfoque es apropiado para una demostración breve pero no permite escalado independiente, alta disponibilidad ni retención durable de señales. La aceptación de ese empaquetado depende de cotejar la guía original de la profesora, que no estuvo disponible en el workspace.

Este documento distingue evidencia local, código preparado y recursos desplegados. No se ejecutaron acciones en cuentas AWS ni Google Cloud. Las cuentas gratuitas mencionadas por la estudiante no se inspeccionaron y no implican costo cero. Los puertos locales nuevos evitan interferir con los contenedores históricos de monitoreo.

Archivos de arquitectura: compose.otel.yml, app/main.py, app/service.py, app/storage.py, app/telemetry.py, otel/ e infra/. Guías de reproducción: GUIA_LOCAL.md y NUBES_COSTOS_Y_ELIMINACION.md. Fecha de consolidación: 2026-10-12 20:26 America/Bogota.

## 2. Instrumentación y señales

La instrumentación automática cubre FastAPI, cliente HTTP httpx y SQLAlchemy. Cada salto crea spans de servidor, cliente y consulta, propagando W3C TraceContext. Los spans personalizados representan creación, lectura, persistencia y actualización de estado. No se agregan documentos o nombres de clientes como atributos de spans ni mensajes de negocio; los datos de carga son sintéticos. Las consultas instrumentadas mantienen parámetros SQL separados.

El SDK configura recursos con service.name y entorno de laboratorio. TracerProvider usa BatchSpanProcessor y exportador OTLP HTTP. MeterProvider emplea un lector periódico con exportación cada cinco segundos. LoggerProvider registra eventos mediante OTLP, además de un handler stdout con formato JSON. Los eventos correlacionados llevan timestamp, nivel, nombre de servicio, trace_id y span_id. Los logs de acceso de uvicorn siguen siendo logs operativos de texto; no se confunden con los registros de negocio exportados.

El Collector versionado aplica memory_limiter antes de resource y batch. El límite de memoria del procesador es 384 MiB, inferior al máximo del contenedor de 512 MiB. OTLP recibe en 4317 y 4318 dentro de la red de laboratorio. Jaeger recibe trazas por OTLP; Prometheus consulta el exporter de métricas en 8889 y las métricas internas de Collector en 8888. Loki ingiere logs mediante su endpoint OTLP nativo y conserva trace_id como metadato estructurado, sin convertir UUID por solicitud en etiqueta de índice.

El dashboard utiliza las métricas históricas para mantener visibilidad durante el baseline sin SDK. Las mediciones SDK no se suman a las métricas equivalentes de /metrics, evitando duplicar el tráfico aparente. El SDK añade CPU acumulada y memoria del proceso; el benchmark usa docker stats por contenedor, una fuente distinta y explícitamente identificada.

OTEL_ENABLED requiere recrear o reiniciar los procesos con la variable cambiada. false desactiva proveedores e instrumentadores, pero los paquetes siguen instalados y /metrics continúa activo. Así se mide el costo de instrumentar y exportar señales sobre el mismo negocio; no se compara una imagen mínima con otra de dependencias diferentes. El Collector permanece encendido en ambos modos.

Las versiones de SDK e instrumentadores pertenecen a la misma familia compatible 1.38.0 y 0.59b0. Collector 0.139.0, Jaeger 1.64.0, Prometheus 3.2.1, Grafana 11.6.0, Loki 3.4.2 y k6 0.57.0 se fijan para reproducibilidad. Las dependencias efectivas se guardan en la evidencia de freeze.

## 3. Pruebas y correlación

La suite unitaria contiene las ocho pruebas existentes y dos adicionales. Las primeras comprueban salud, métricas, UUID, estado PENDING, listado, consulta, 404, actualización y rechazo de estado inválido. Las nuevas ejercitan el adaptador HTTP y su traducción de fallos de transporte a 503. El resultado dentro de Docker fue diez pruebas exitosas; las advertencias de deprecación de TestClient se conservan en el registro. Antes de modificar, el Python host no pudo colectar la suite por una dependencia ausente, de modo que no se afirmó una línea base exitosa en ese entorno.

La integración real utiliza la API publicada localmente y un traceparent sintético. Comprueba creación, lectura, listado, actualización, 404, validación 422 y persistencia después de reiniciar B. Consulta Jaeger y exige una traza con procesos service-a y service-b y un span identificado como PostgreSQL. Consulta Loki por el proxy autenticado de Grafana y exige registros correlacionados de ambos servicios. Verifica además los targets Prometheus y el dashboard provisionado de seis paneles. El resultado fue 13 comprobaciones exitosas.

El trace_id registrado en esta consolidación es 868d7e4a569d404cb1dcfa718703ab90. El archivo trace.json contiene los spans y procesos reales; logs.json contiene el resultado de Loki; validation.json enumera las aserciones. Esta evidencia es verificable sin depender de una captura de pantalla o una afirmación verbal. Los campos trace_id y span_id en registros OTLP son metadatos estructurados y se correlacionan con la traza del backend.

Las métricas son agregadas: no se afirma que compartan un trace_id por cada muestra. El servicio y la ventana temporal permiten contextualizar un pico de latencia frente a trazas y logs. Se configuró un destino para exemplars y un enlace desde trace_id a Jaeger, pero la navegación visual de exemplars y del enlace no se declaró comprobada automáticamente.

Una prueba adicional detuvo solamente B y comprobó que A devolviera 503 con el mensaje Credit storage unavailable. Un bloque finally restauró B y esperó su salud. No se borraron datos ni se manipularon los contenedores históricos. La evidencia failure.json conserva el código, respuesta y trace_id de esa falla.

Las capturas GUI y la cotejación con oTelLabs.zip siguen siendo trabajo editorial o de validación externa. El workspace carece de .git: los archivos están preparados pero no se creó rama ni se publicó repositorio. Estos pendientes no se convierten en resultados completados.

## 4. Benchmark y resultados

Se ejecutó carga constante de cincuenta usuarios virtuales durante cinco minutos en cada modo, precedida por veinte segundos de warm-up. Cada iteración consulta un crédito sintético y actualiza su estado. Los modos comparten UUID, volumen, dependencias y límites por aplicación de un core y 512 MiB. El dataset queda acotado para que el listado creciente o la creación continua no distorsionen la comparación. Las métricas HTTP incluyen nombres estables read/update, evitando series por identificador.

Se midió el p99 de duración HTTP mediante k6. Los JSON resumen conservan además distribución, requests y tasa de errores. Las muestras de docker stats registran timestamp UTC, servicio, CPU porcentual y memoria MiB. CPU representa porcentaje de un core; los promedios A y B se suman para estimar el consumo de aplicaciones. El Collector se reporta aparte para no confundir costo de SDK con costo de procesamiento de señales. Las muestras individuales están disponibles en CSV.

Resultado sin SDK: p99 680.39 ms, 24784 solicitudes y tasa de fallo 0.0000%. Resultado con SDK: p99 2026.96 ms, 16396 solicitudes y tasa de fallo 0.0000%. Diferencia p99: +1346.56 ms, equivalente a +197.91% respecto al baseline.

CPU media A+B: 143.74% sin SDK y 165.91% con SDK. El cambio relativo es +15.42%. Memoria media A+B: 173.25 MiB frente a 199.03 MiB; diferencia +25.78 MiB (+14.88%). Estas cifras no describen CPU del host completo ni memoria RSS de un único proceso.

Se conservó un primer par exploratorio que coincidió con preparación de Terraform. El par final se ejecutó después de terminar instalaciones, builds y validaciones, sin tareas de preparación simultáneas. Los contenedores históricos de monitoreo siguieron activos en ambos modos. El orden fue sin SDK seguido de con SDK; una pareja final no permite calcular intervalos de confianza ni eliminar sesgos de caché y orden. Para estimación estadística se recomienda repetir y alternar orden.

OTEL_ENABLED=true se restauró al finalizar. La prueba controlada de fallo es funcional y no una carga de cinco minutos con fallas. No se reportaron benchmarks cloud. Los resultados son observaciones de este host Windows/Docker y este workload, sin generalizar a producción.

## 5. Infraestructura, costos y reversión

AWS prepara una VPC con una subnet pública para ECS y dos privadas para RDS; security groups restringen el acceso al gateway al IPv4 /32 aprobado de la estudiante y PostgreSQL a la tarea. Una tarea Fargate con dos vCPU y cuatro GiB agrupa ocho contenedores. RDS PostgreSQL administra la persistencia; Secrets Manager entrega la contraseña a B sin incorporarla a la imagen. Se preparan seis ECR, un grupo CloudWatch Logs y roles IAM de ejecución y tarea. No se incluyen NAT Gateway ni ALB.

Google prepara un servicio Cloud Run con ocho contenedores de un vCPU cada uno y memoria total de 4 GiB. CPU siempre asignada y una instancia mínima sostienen Collector y scrapes de fondo. Cloud SQL mantiene PostgreSQL mediante socket de conexión autorizado; Artifact Registry almacena imágenes derivadas. Secret Manager contiene DB y Grafana y la cuenta de servicio recibe permisos limitados de SQL y secretos. El ingreso requiere IAM run.invoker para una identidad concreta; no se asigna allUsers.

Las imágenes auxiliares incorporan la configuración cloud y usan localhost porque los contenedores comparten el namespace de red de una tarea/instancia. El gateway expone API y rutas de interfaces; OTLP y DB quedan fuera del ingreso público. La configuración local utiliza DNS de Compose y no se confunde con esta excepción del empaquetado cloud. La separación por contenedores no aporta escalado independiente: cotejar ese punto con la guía original.

Terraform validate se ejecuta en Docker sin backend y sin credenciales. La validación confirma estructura de recursos y expresiones; no confirma cuotas, permisos efectivos, disponibilidad regional ni arranque remoto. Los providers se fijan mediante lockfiles. Un problema inicial de arranque del provider sobre el bind mount Windows se resolvió con un volumen Linux. No se ejecutaron terraform plan/apply con cuentas.

El costo orientativo de cómputo es US$0.0987/h para Fargate y US$0.5472/h para Cloud Run, antes de RDS/Cloud SQL, discos, secretos, registries, logs, red e impuestos. La cuota o crédito gratuito del usuario no se verificó. Cloud Run con minimum instances=1 y las bases de datos generan costo aunque nadie utilice la API. Consultar las fuentes oficiales y una cotización regional antes de aprobar.

La reversión requiere exportar evidencias y créditos necesarios, aprobar el plan de destroy y borrar únicamente los recursos propios. ECR no fuerza eliminación de imágenes; hay que autorizar su limpieza. El secreto Grafana externo AWS no pertenece al estado y no debe borrarse si era preexistente. Las APIs GCP y el proyecto compartido se conservan. Ambas DB permiten borrado sin protección para demostración: destroy pierde datos. Nada de esto se ejecutó en nube.

## 6. Conclusiones y entrega

La adaptación local cumple la cadena de dos procesos HTTP y PostgreSQL, mantiene los contratos de créditos y ofrece instrumentación automática y personalizada. Las tres señales llegan a backends consultables: trazas en Jaeger, métricas en Prometheus y logs en Loki. Grafana provisiona fuentes y seis paneles. La evidencia incluye una traza común de A/B/DB y registros correlacionados, pruebas funcionales y mediciones de carga. La conclusión se limita a ejecuciones locales comprobadas.

Las pruebas unitarias se reproducen en la imagen construida con Dockerfile, montando tests en solo lectura. La integración se reproduce con python scripts/validate_local.py. El benchmark se reproduce con python scripts/benchmark.py y tarda más de diez minutos. Terraform se valida mediante scripts/validate_infra.ps1. La documentación conserva comandos para detener el stack con stop y preservar volúmenes, evitando acciones destructivas como down -v o prune.

La entrega consta de código actualizado, compose.otel.yml, configuraciones OTel/backends, dashboard, scripts de prueba, IaC AWS/GCP, lockfiles y carpeta docs/evidence. ESTADO_FINAL.md enumera por requisito implementación, prueba, archivo, pendiente, riesgo y siguiente paso. GUIA_LOCAL.md explica la operación; NUBES_COSTOS_Y_ELIMINACION.md documenta recursos y costos sin desplegarlos. Este informe tiene seis secciones paginadas y no sustituye las evidencias de ejecución.

Pendientes: obtener y revisar oTelLabs.zip y rúbrica original; confirmar si dos microservicios agrupados en una tarea/instancia satisfacen la evaluación; revisar autores y capturas complementarias; restaurar o inicializar Git con autorización de publicación; repetir más pares de carga para incertidumbre estadística; verificar navegación de enlaces y exemplars en la interfaz. Ninguno de estos pendientes se oculta ni se marca como cumplido por tener archivos preparados.

El criterio de Collector desplegado en ambas nubes no está satisfecho. Para cumplirlo se necesita aprobar una propuesta concreta con cuenta/proyecto, región, presupuesto, duración, imágenes y plan Terraform. Después del despliegue autorizado deberán repetirse CRUD, trazas y logs y registrar recursos activos. Las cuentas disponibles no son evidencia de despliegue. El objetivo actual terminó en infraestructura revisable, no en aprovisionamiento remoto.

La seguridad del laboratorio evita secretos versionados y datos personales en telemetría. Los ejemplos locales se publican solo en loopback. La configuración cloud distingue ingreso IAM en GCP y CIDR restringido AWS; AWS sin HTTPS es únicamente una demostración con datos sintéticos. Los estados Terraform que contengan contraseñas deben protegerse y no adjuntarse a la entrega.

Fecha de consolidación: 2026-10-12 20:26 America/Bogota. Evidencias principales: validation.json, trace.json, logs.json, targets.json, failure.json, benchmark.json, summaries/CSV de ambos modos y terraform-*-validate.json. Los valores reportados son los guardados en esos archivos, sin datos inventados ni ejecución cloud supuesta.