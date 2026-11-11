# Evidencia local del portal — 6 de noviembre de 2026

Entorno: macOS, Python 3.12, Chrome real mediante Playwright, PostgreSQL/Redis/
MongoDB temporales aislados, TLS de prueba con certificado local. Sin cambios en
instalaciones habituales, sin datos personales reales, sin despliegue GCP.
El manifiesto `sources.json` identifica las fuentes del incremento; no se creó commit.

## Resultados por ejecución

| Archivo | Resultado | Alcance |
|---|---|---|
| `tracking.xml` | 2 aprobadas, 16 errores de preparación | Sandbox no ejecutó MongoDB; no acredita integración |
| `tracking-final.xml` | 17 aprobadas, 1 fallo | WSS JSON/XML/replay/revocación/caídas/concurrencia; fallo del caso nuevo por cuenta `operator3` inexistente |
| `portal-attempt.xml` | 1 fallo | Mismo error del verificador; corregido a transportista ajeno existente |
| `portal-final.xml` | 1 aprobada, 1 fallo | Ticket/CSRF/privacidad/publicación denegada aprobados; navegador falló por CSP de su servidor TLS temporal |
| `browser-recovery.xml` | 2 aprobadas | Chrome siete perfiles y SMTP real local; corrección de orden del hook CSP de prueba |
| `browser-reconnect.xml` | 1 aprobada | Repetición del navegador exige incremento de conexiones y estado en vivo; no suma otro caso único |
| `agenda.xml` | 1 fallo | Verificador usó argumento `params` no soportado por Platform.request; formularios previos sí persistieron |
| `agenda-final.xml` | 1 aprobada | Consentimiento, horario, reserva, confirmación y cancelación mediante web con lectura persistente |
| `unit.xml` | 15 aprobadas | Regresión unitaria existente `test_review_unit.py` |
| `regression.xml` | 27 aprobadas, 479,77 s | HTTP, web autónoma sin API, sangre/órgano/donación y operaciones de agenda |

Los cuatro casos nuevos y los 17 WSS más 15 unitarios más las 27 de integración dan **63 identidades
aprobadas**, sin sumar repeticiones. Cada XML conserva duración y casos exactos.
Los fallos originales siguen visibles y no se describen como ejecuciones limpias.

`browser/browser.json` registra ocho comprobaciones agrupadas: siete paneles en
390/768/1440 y mapa WSS con reconexión/capas/degradación. Capturas PNG en esa carpeta.
Se inspeccionó visualmente la captura móvil. No certifica contraste de toda la
aplicación ni todos los recorridos de cada perfil. Se bloquearon mosaicos en las
pruebas automatizadas para respetar la política de OSM: demuestra degradación,
no una validación visual de mosaicos en línea. El socket usa TLS real contra
Transporte; un override exclusivo del test dirige la ruta de gateway al puerto
TLS temporal. No se presenta como ensayo del reverse proxy de producción.

## Comandos y límites

[Comandos reproducibles y guía](../../../entrega-final/portal/Operacion.md).
El entorno de este Mac requirió `REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"`
y permiso para procesos/puertos locales fuera del sandbox. Chrome se habilita
explícitamente con `REDHOUSE_BROWSER_TESTS=1` en ejecuciones futuras.

Generación de contratos, `document.py --check-openapi`, sintaxis JavaScript, Ruff
crítico, formato de archivos nuevos y `git diff --check` aprobados. Se actualizaron
solo las restricciones de formularios de agenda afectadas; el exportador completo
incluye diferencias previas de otras operaciones y no se declara su check global.

Pendientes técnicos y externos separados en la [matriz](../../../entrega-final/portal/Matriz.md).
No se considera terminado el prompt 03.
