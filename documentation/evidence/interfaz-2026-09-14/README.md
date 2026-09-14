# Revisión de textos y navegación — 14 de septiembre de 2026

## Resultado

**89 pruebas aprobadas, sin fallos, errores u omisiones; 94.92 segundos según JUnit.**

Se ejecutó la suite completa con PostgreSQL exclusivo y Chrome. Cada prueba creó y retiró su propia base temporal; los expedientes y las cuentas de la instalación habitual se conservaron. El clúster exclusivo se detuvo al terminar. El monolito actualizado quedó disponible en el puerto 5050.

## Criterios comprobados

- Donantes, receptores, donaciones, solicitudes, rutas y traslados seleccionan su propia sección; las páginas de detalle conservan la selección. Un solo enlace tiene `aria-current="page"`.
- El Auditor identifica su sección de trazabilidad y el Coordinador no recibe dos enlaces a la misma página de traslados.
- El menú móvil abre, muestra el enlace activo y cierra; pantallas de 1440 y 390 px sin desbordamiento de página.
- Etiquetas operativas en formularios; ausencia de frases académicas generales y traducción de estados como Elegible. La traducción se limita a campos de estado/tipo, no a nombres, folios ni observaciones guardadas.
- Flujo completo donante → recepción → cierre, permisos, autorización humana, incompatibilidad, concurrencia y auditoría continúan aprobando.
- Chrome sin errores JavaScript ni recursos locales faltantes. Órganos indica que no está disponible; recuperación de acceso remite al administrador.
- Comprobación HTTP posterior al reinicio: salud 200, acceso del Operador, Donantes con enlace activo correcto y etiquetas actualizadas; cierre de la sesión de comprobación.

## Evidencias

- [Tests.xml](Tests.xml): resultados de la suite.
- [Donantes, escritorio](regional/Donantes_lista_vista.png).
- [Donantes, menú móvil](regional/Donantes_navegacion_mobile_vista.png).
- [Expediente y evaluación](regional/Donante_revision_vista.png).
- [Compatibilidad y autorización](regional/Compatibilidad_priorizacion_vista.png).
- [Capturas del flujo regional](regional/).

Las capturas contienen datos ficticios generados por las pruebas. Los nombres de instituciones, cuentas y componentes de la carga original pueden contener DEMO: son valores registrados, no etiquetas de interfaz. El código y la versión del motor y el aviso de compatibilidad demostrativa permanecen identificables. Los reportes y capturas del 13 de septiembre conservan su condición de corte histórico; esta revisión cambia presentación y navegación.

## Reproducción

Desde `apps/web-monolito01`, definir `TEST_POSTGRES_URL` hacia un clúster exclusivo con permiso para crear bases, `NODE_PATH` hacia Playwright y `BROWSER_ARTIFACTS` hacia un directorio nuevo. Chrome debe estar instalado.

```sh
python -m pytest -q --browser -p no:cacheprovider --tb=short --junitxml=/ruta/nueva/Tests.xml
```
