# iOS B: cierre Qt/web y conservación sintética — 17/11/2026

**Cierre compuesto iOS→Qt/XML→web aceptado por dirección: recepción, descarte documental y Chrome terminaron con salida 0; el oráculo global de solo lectura aprobó 112 controles.** No se declara etapa 07 completa, conservación física acreditada ni habilitación clínica.

El mismo riñón sintético `097cb5d9-fc8a-4a61-9050-815a4bb3c357`, traslado `5b90b104-888a-4adf-9ab5-5df40a686ac0`, reserva `2d494368-3c5a-4458-b358-62803c767d44`, solicitud `15163544-0aa1-4b9f-83dd-8dacc83b543f` y receptor `889fe2fb-5a95-4012-a2d6-aeb2ada72446` continúan desde iOS hacia Qt/XML y el monolito web. Se reutilizan [laboratorio del receptor](../desktop/ios-b-laboratorio-receptor-20261117/RESULTADOS.md), [receptor/solicitud](../desktop/ios-b-receptor-solicitud-20261117/RESULTADOS.md) y [evaluación/reserva/planificación/preparación](../desktop/ios-e2eb-allocation-origen-20261117/RESULTADOS.md); no son nuevas ejecuciones de esos tramos.

## Composición comprobada y límites

| Tramo | Evidencia existente | Alcance |
| --- | --- | --- |
| iPhone físico | Usuario confirmó entrega y ubicación detenida; el gate previo leyó DELIVERED v5, mismo QR/sello IOSB-17 y contraparte. Foto LOCAL `a0850689-0b13-416e-bb9c-b5569bd3683b` verificada con generación/hash y ClamD; evento GPS IOS `0b868dd5-687e-4f4d-865d-a88051ee060c` observado en servidor. | No se repiten cámara, GPS o custodia. Evento observado no equivale a ACK capturado del dispositivo ni certifica latencia. Oráculo global posterior aceptado con el alcance descrito abajo. |
| Recepción Qt/XML | [Formulario real](recepcion-qt.png), operator2; ACCEPTED v6, una transición, un evento fuente y una proyección en Custodia/Auditoría; familia propia cerrada SQL/Redis. | Dirección aceptó recibo y captura. Gate exigió DELIVERED v5, controles desbloqueados y última lectura ≤ 300 s; backend volvió a validar custodia/calidad. |
| Destino Qt/XML | [Formulario real](destino-qt.png), medical2 con MFA/reautenticación; DISCARDED v1, evento único, unidad WITHDRAWN y familia propia cerrada. | Referencia `IOSB-DESCARTE-SINTETICO-20261117`; motivo «Descarte académico de unidad sintética; sin uso clínico». Sin implante ni uso clínico. |
| Chrome final | Cinco GET 200, cero errores JavaScript, únicamente login/logout, una familia propia cerrada; negocio y fuentes iguales antes/después. | Dirección inspeccionó las cinco capturas. Misma unidad retirada, traslado aceptado, solicitud cerrada/cobertura recibida y conservación con 18 lecturas/2 brechas. |

Las capturas web muestran [recurso retirado](01-recurso.png), [formulario de destino](02-destino.png), [traslado aceptado/cadena 1–6](03-traslado.png), [solicitud cerrada](04-solicitud.png) y [conservación](05-conservacion-brecha.png). El GET de destino abre un formulario para corregir: Descartado aparece seleccionado, pero referencia y motivo previos no se cargan en los campos nuevos, intencionalmente vacíos y no enviados. Esa imagen no prueba los textos históricos; los recibos Qt/SQL sí los conservan.

## Dos brechas conservadas y revisión humana

El perfil sintético existente mantuvo intervalo máximo 300 s; no se alteraron reglas, fechas, caducidad ni reloj. Las 18 lecturas están identificadas como sintéticas. La primera conserva la fuente `ACADEMICO MANUAL SINTETICO; valor generado del perfil; NO medicion fisica`; las otras 17 indican `SIMULACION TERMICA ACADEMICA; NO MEDICION FISICA`. Sus valores de 1.5 °C pertenecen al perfil sintético de 1–2 °C. Son datos académicos, no mediciones de un equipo físico.

La primera nueva lectura conservó una brecha, bloqueó controles y llevó AVAILABLE a QUARANTINE. Medical1 documentó revisión explícita y luego una liberación separada. El soporte finito registró 15 lecturas únicas con reloj real, cadencia 60 s y duración 841.91 s; no rellenó intervalos pasados ni reenvió intenciones anteriores. Al finalizar la ventana se permitió que el tiempo real transcurriera.

Antes de recepción, otra lectura vigente registró una segunda brecha real del ensayo: la unidad seguía IN_TRANSIT, por lo que conservó ese estado y quedó bloqueada. La nueva acción Qt «Revisar incidente» registró la segunda revisión médica, desbloqueó controles y mantuvo IN_TRANSIT; no hizo otra liberación. El cierre conserva 18 lecturas, 2 brechas, 0 excursiones, 2 revisiones de incidente y 2 liberaciones documentadas. Ambos pares completos brecha/revisión se comprobaron por UUID/huella antes y después de las etapas finales. La interfaz Conservación muestra lecturas y bloqueo actual; la revisión histórica se acredita por Qt/SQL, no por una lista de revisiones inexistente en esa página.

## FAIL del soporte preservado y cierre conciliado

El [recibo original](support-wrapper-FAIL-original.json) permanece `passed=false`: el wrapper exigió una familia nueva, pero el oráculo encontró dos familias de operator1 creadas desde su snapshot. Una pertenece al soporte y otra a la preparación Qt de origen ejecutada durante esa ventana. El helper ya había verificado revocación SQL y ausencia de las dos claves Redis; después falló `assert len(closed)==1`.

La [conciliación derivada de solo lectura](support-reconciliation.json) verificó nuevamente exactamente esas dos familias: ambas revocadas y ausentes de Redis. Contrastó snapshots y el recibo Qt, que contiene únicamente su propia familia. No inició login/logout, nuevas lecturas ni replays; no cambió el FAIL original ni afirma el estado de todas las sesiones del sistema. Quince lecturas aceptadas y cierre conciliado se presentan como evidencia compuesta, no como salida 0 del wrapper original.

## Oráculo global aceptado y fallos previos conservados

El [oráculo global saneado](global-oracle.json), aceptado por dirección, aprobó 112 comprobaciones: 49 eventos fuente correlacionados con 49 registros de auditoría SQL y 49 Mongo; 13 avisos encontrados/13 esperados. Confirma unidad retirada en destino, reserva recibida, solicitud/receptor, constancia/evaluación/dictamen, transiciones, foto LOCAL/CLEAN vinculada, GPS IOS/outbox/Mongo, seguimiento inactivo y ambas brechas/revisiones. Es consulta posterior de solo lectura, compuesta con el ensayo humano y las capturas Qt/web; por sí sola no acredita lectura QR óptica ni inspección de interfaz. Solo se normalizó received_at al mismo instante UTC.

Se conservan [dos arranques previos fallidos](global-preflight-failures.json), ambos anteriores a SELECT y sin mutaciones: permisos privados 0644 rechazados frente a 0600 y ps bloqueado por sandbox. La ejecución final del mismo comando revisado, con escalación local, terminó exit 0. No se convierten esos rechazos en ejecuciones exitosas ni se repitió negocio.

## Pendientes visuales comunes y límites

Dirección detectó dos defectos visuales vigentes: `RESOURCE_COLD_QUARANTINE` aparece como «Evento sin clasificación» y Conservación de un órgano activa «Inventario sanguíneo» en navegación. Se registran para el lote visual común; durante el ensayo no se modificó producto con el runtime abierto. Ese runtime ya cerró con salida 0 y cierre de procesos propios confirmado, conservando fuentes, configuración, objetos y cambios del caso, sin reset. El [recibo saneado del cierre](runtime-closure.json) mantiene la huella del original privado. El alcance del GET de destino descrito arriba también se conserva sin atribuirle lectura de campos históricos.

El [resumen verificable](resumen.json) conserva hashes de recibos privados y copias públicas, sin credenciales, factores, tokens, diarios o URLs privadas. Variantes restantes, latencia conjunta, accesibilidad, otras plataformas, carga, push y validación clínica mantienen su aceptación separada. Esta consolidación no hizo operaciones GCP, reinicios, reset/seed ni nuevas ejecuciones funcionales.
