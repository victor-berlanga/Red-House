# Pantallas, tareas y autorización del portal

Revisión 06/11/2026. Los controles del menú ayudan a navegar; la autorización efectiva
se ejecuta en el propietario de cada contrato. Toda petición privada valida JWT, sesión
y permisos vigentes en Redis, además del ámbito del recurso. El modo modular utiliza
estos mismos propietarios sin listeners HTTP. Las rutas API siguientes llevan `/api/v1`.

| Perfil | Pantalla/tarea | Propietario y contrato | Ámbito y rechazo exigido |
|---|---|---|---|
| Público | `/`, instituciones/campañas publicadas | Identidad `/public/institutions`; Donantes `/public/campaigns` | Solo publicación explícita, campos mínimos; sin coordenadas privadas ni expedientes. |
| Todos | `/login`, `/recuperar-acceso`, `/recuperar-acceso/confirmar`, `/logout` | Identidad `/auth/login`, `/auth/recovery`, `/auth/recovery/complete`, `/auth/revoke` | MFA según política; token de recuperación de un uso; cierre durable y revocación. |
| Todos | `/panel`, preferencias de horario, avisos | Cada propietario `/portal-metrics`; Alertas `/alerts` | Rol/ámbito vigentes; métricas operativas no conceden expedientes clínicos. |
| Donante | `/donantes/donor`, alta/edición permitida y evaluación | Donantes `/donors`, `/donors/{id}` | Usuario vinculado a expediente, institución; donante ajeno rechazado. |
| Donante / médico | `/donantes/donor/{id}/consentimientos` | Donantes `/donors/{id}/consents` | Donante propio o facultad médica institucional; nuevas versiones, no reemplazo de historia. |
| Donante / operador | `/campanas`, horarios, `/citas` | Donantes `/campaigns`, `/campaign-slots`, `/appointments` | Cupos bajo bloqueo, cita propia del donante; asistencia solo por operador. |
| Operador | Campaña → publicación y horarios | Donantes `/campaigns/{id}/publication`, `/campaign-slots` | Institución, versión, sede autorizada; no publicación automática. |
| Médico / operador según paso | `/donaciones`, registro y procesamiento | Donantes `/donations`, `/donations/{id}/steps` | Evaluación humana, consentimiento y proceso vigente; no inventar elegibilidad. |
| Operador | `/inventario/nuevo`, componentes, linaje, etiqueta | Inventario `/resources`, `/resources/{id}/components`, `/resources/{id}/lineage` | Origen procesado y pertenencia; componentes en cuarentena. Código no equivale a liberación. |
| Operador / médico | Inventario, movimientos, ubicaciones y caducidad | Inventario `/resources`, `/resources/{id}`; Identidad catálogos | Institución actual; el origen pierde acceso al recurso transferido cuando corresponde. |
| Operador | Conservación → equipos/lecturas | Inventario `/cold/equipment`, `/resources/{id}/cold-readings` | Captura propia; no facultad de revisión médica. |
| Médico | Perfiles térmicos, controles y revisión | Inventario `/cold/profiles`, `/resources/{id}/controls`, `/quality-review` | Versiones y confirmación; perfil sintético explícito; revisión no libera. |
| Operador / médico | `/laboratorio/muestras`, recepción, resultados/corrección | Compatibilidad `/laboratory/samples`, `/laboratory/results` | Captura dentro del ámbito institucional; historia por versión y sujeto. |
| Médico | Revisión de resultado y liberación | Compatibilidad `/laboratory/results/{id}/review`; Inventario `/resources/{id}/release` | Reautenticación configurada, versión, completitud y fuentes; operador/administrador rechazados. |
| Médico | Receptores y solicitudes | Receptores `/recipients`, `/requests` | Expediente clínico institucional; coordinador solo recibe proyecciones logísticas autorizadas. |
| Médico | Solicitud → constancias externas | Receptores `/requests/{id}/external-authorizations` | Vigencia, autoría, versión anterior y confirmación; registro no emite autorización oficial. |
| Médico | Evaluación, dictamen, reserva | Compatibilidad `/evaluations`, `/evaluations/{id}/reviews`; Inventario `/reservations` | Candidato actual, revisión humana, reautenticación y capacidad única; HLA faltante no aprueba. |
| Médico | Operación pendiente → seguimiento/reanudar | Inventario `/operations/{id}`, `/operations/by-key/{key}`, `/operations/{id}/resume` | Mismo usuario, clave, huella y ámbito; no repetir efectos ni cambiar backend. |
| Médico | Crear propuesta de cobertura | Prioridad `/allocation-proposals` POST | Solo evaluación propia revisada; no crea reservas automáticamente. |
| Coordinador | Consultar propuestas regionales | Prioridad `/allocation-proposals` GET y detalle | Identidad determina instituciones regionales; sin instantáneas clínicas ni permiso de creación/dictamen. |
| Coordinador | Rutas, programar traslados, emisor por orden | Geografía `/routes`; Transporte `/shipments`, `/tracking/assignments` | Región, responsables, disponibilidad y versión; emisor pertenece al transportista. |
| Transportista | Orden asignada, recolección/tránsito/entrega/incidencia | Transporte `/shipments/{id}/transitions`; Custodia | Solo responsable vigente; escaneo/sello/contraparte/aceptación según paso. Otra orden no se autoriza por conocer UUID. |
| Operadores origen/destino | Preparación y aceptación | Transporte `/shipments/{id}/transitions` | Institución correspondiente al paso; no confundir entrega con aceptación ni uso. |
| Médico destino | `/inventario/{id}/destino` | Inventario `/resources/{id}/destination` | Institución actual, tipo de recurso, recepción previa, reautenticación e historia aditiva. |
| Coordinador / transportista / operador / médico autorizado | `/traslados/{id}/mapa` | Transporte `/shipments/{id}/tracking/snapshot`, `/tracking/ticket`, WSS JSON | Región/institución/asignación vigente; ticket solo lectura de una orden; autorización continua. |
| Administrador | `/configuracion`, presentación y política | Identidad `/institutions/{id}/presentation`, `/portal-policy` | Propia institución, CAS/versiones y auditoría; sin elevación clínica. |
| Administrador | Dispositivos: alta, credencial, revocación | Identidad `/devices` y acciones | Responsable transportista de su institución; secreto de un uso, no mostrar en capturas/logs. |
| Perfil del sujeto | `/documentos`, carga/versiones/análisis | Documentos `/documents`, `/documents/{id}/status`, `/files/{id}/verify` | Autoridad del sujeto subyacente en cada operación; archivo pendiente/rechazado bloqueado. |
| Administrador / médico autorizado | Documento → conservación/bloqueo | Documentos `/documents/{id}/conservation` | Misma autorización del sujeto, versión de política y bloqueo; no suponer plazo legal. |
| Perfil autorizado del reporte | `/reportes`, nuevo/reintentar/descargar | Documentos `/export-jobs`, `/files/{id}/download` | Reautoriza creación, extracción y descarga; contexto cifrado temporal; sin URL pública alternativa. |
| Auditor | `/auditoria`, filtros, detalle, vínculos, exportación | Auditoría `/events` y consultas relacionadas | Región, minimización de contenido y autorización real de exportación. |
| Auditor / coordinador asignado | `/hallazgos` y acciones | Auditoría `/findings`, `/findings/{id}/actions` | Responsable atiende; auditor verifica. Historia inmutable, conflictos de versión y no cierre por responsable. |
| Administrador / rol autorizado | Salud/configuración técnica | Monitoreo `/status` y estados de dependencias | Diagnóstico minimizado; readiness no sustituye prueba de negocio. |

Las facultades de laboratorio quedan explícitas: captura/recepción por `OPERATOR` o
`MEDICAL` según contrato; revisión, dictamen y liberación exclusivamente `MEDICAL`.
No se creó una facultad clínica implícita en `ADMIN` ni se amplió la lectura clínica
del coordinador. Los tests positivos y negativos se vinculan en [Matriz.md](Matriz.md).
