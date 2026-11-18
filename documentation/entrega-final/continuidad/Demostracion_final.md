# Índice operativo de demostración final

Estado de corte: documentación de apoyo en curso. Este índice ordena evidencia existente; no afirma una ejecución final integrada, aceptación académica ni entrega completa. Los recorridos registrados usaron datos sintéticos y entornos de laboratorio salvo cuando la evidencia indique otro alcance.

## Orden sugerido

1. **Ingreso de unidad y revisión de laboratorio.** Operador recibe una muestra y captura resultado; personal médico autorizado revisa. La ejecución Qt/XML verificó persistencia, versión, vínculo por muestra y auditoría. [Resultados](../../evidencias/entrega-final/desktop/iteracion-laboratorio/RESULTADOS.md) · [matriz de continuidad](Matriz.md).
2. **Solicitud, evaluación y reserva revisada por persona autorizada.** Mostrar consulta de candidato, vigencia, dictamen humano y reserva; separar el resultado algorítmico de la decisión. El ensayo de evaluación fue Qt/XML con solicitud y unidad sintéticas; la reserva comprobó recuperación con la misma clave y una sola reserva. [Evaluación](../../evidencias/entrega-final/desktop/iteracion-evaluacion/RESULTADOS.md) · [reserva y límites](../../evidencias/entrega-final/desktop/iteracion-reserva/RESULTADOS.md).
3. **Traslado y cadena de custodia.** Mostrar tarea del transportista, lectura QR, transiciones de recolección/tránsito/entrega y aceptación del destinatario. La ejecución Android aprobó el recorrido sintético y contrastó eventos en SQL/Mongo; no demuestra GPS físico, cámara física ni una prueba física de teléfono. [Resultados móviles](../../evidencias/entrega-final/mobile/RESULTADOS.md) · [estado del 14/11](../../../PROJECT_STATUS.md) · [matriz móvil](../../entrega-final/mobile/Matriz.md).

Los tres ensayos son evidencias separadas; la secuencia no se ha aceptado como una única demostración integral ni acredita por sí sola los tres flujos integrales exigidos. Antes de grabar, confirmar la versión desplegada siguiendo el [procedimiento GCE](../../../deployment/gcp/README.md). El paquete actual de escritorio es [macOS Intel](../../evidencias/entrega-final/desktop/paquete-mac-20261114/RESULTADOS.md); los paquetes móviles constan en el [registro de compilación y firma](../../evidencias/entrega-final/mobile/seguimiento-20261114/paquetes.md).

## Guion del video (temas que pide la consigna)

Video breve, unos 10 a 12 minutos. Grabar contra la VM encendida (`https://34.18.186.116`), con cuentas sintéticas y **sin mostrar contraseñas ni códigos MFA** (pausar la grabación al iniciar sesión). Pasos de prueba y cuentas: [guía de prueba manual](../../markdowns/Guia_prueba_manual.md).

| # | Tema | Qué mostrar | Dónde |
|---|---|---|---|
| 1 | El problema | Información dispersa entre bancos de sangre y hospitales; demoras y falta de trazabilidad | Reporte técnico, sección 2 |
| 2 | La arquitectura | Diagrama: portal, 12 servicios, PostgreSQL, MongoDB, Redis, GCS, Nginx; JSON para móvil, XML para escritorio | [despliegue.svg](../modelos/diagramas/despliegue.svg), reporte sección 4 |
| 3 | El sistema web | Panel por perfil; inventario, solicitud y traslado | Portal, proceso 1 de la guía |
| 4 | La aplicación móvil | Transportista: tarea, escaneo, sello, entrega y mapa; donante: reservar cita | App Android (APK del Release) |
| 5 | La aplicación de escritorio | Médico u operador: muestras, resultados, colecta y reporte en XML | Consola PySide6 |
| 6 | Los microservicios | Los 12 servicios con dos réplicas; `/health/ready` de cada uno | `sudo python3 /opt/redhouse/deployment/gcp/fallo.py estado` |
| 7 | Swagger | Swagger UI de un servicio y una operación con su contrato | `https://34.18.186.116/services/inventario/docs/` |
| 8 | El monitoreo | Panel «Estado de la plataforma» y «Diagnóstico técnico» (con `auditor1`) | Portal |
| 9 | La nube | Consola GCP: VM, IP estática, firewall 80/443 y bucket GCS con objetos privados | Consola de Google Cloud |
| 10 | El algoritmo | Evaluación de candidatos: entradas, puntaje explicado y decisión humana | Reporte sección 9, [Algoritmos](../../markdowns/Algoritmos.md) |
| 11 | Las pruebas de carga | Gráficas y tabla de Locust: usuarios, RPS, p95/p99, errores | [Resultados de carga](../../evidencias/entrega-final/) más recientes, reporte sección 15 |
| 12 | La integración | Un proceso completo que cruza web → móvil → escritorio, y la bitácora de Auditoría con cada paso | Procesos 1 a 3 de la guía |

Cierre sugerido: un fallo en vivo (`fallo.py microservicio` y `restablecer`) para mostrar detección y recuperación.

## Quién debe participar

El equipo asigna integrantes y confirma autoría; este documento no atribuye nombres ni contribuciones. Perfiles para el recorrido: operador de laboratorio, personal médico autorizado, coordinador y transportista. Una persona del equipo presenta y otra registra incidencias si el grupo así lo decide. Las reflexiones deben redactarlas y aprobarlas sus autores.

## Pendientes antes de declarar cierre

- Firma iOS: [ambos perfiles renovados](../../evidencias/entrega-final/mobile/profile-renewal-20261117/RESULTADOS.md) vencen el 24/11 y cubren el 23. Normal/Lab fueron actualizadas; normal sigue sin apertura/recorrido y Lab conserva aceptación física parcial. [Comprobaciones y límites](../../evidencias/entrega-final/mobile/ios-current-20261117/RESULTADOS.md). No repetir builds por esta consolidación.
- Windows 11 de escritorio sin verificación; el runner Windows de CI no sustituye la prueba en el equipo destino.
- Recepción física de FCM/APNs pendiente externa y sin cuentas configuradas por decisión del equipo.
- Grabar y conservar el video final, hacer la exposición, recibir reflexiones individuales y confirmar la subida a Ubiquitous. Son entregas humanas; no se sustituyen por este guion ni por evidencia del segundo parcial.
- No publicar credenciales, archivos privados, tokens ni pantallas con datos sensibles. La aprobación clínica/normativa sigue fuera del alcance de estos ensayos sintéticos.
