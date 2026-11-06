# Guion de la nueva grabación — GCP, 4 de noviembre de 2026

Destino: https://34.18.186.116. Versión publicada 0.4.4/esquema 16. Datos ficticios; operación académica.

## Navegación prevista

1. Portal público → Acceso institucional → autenticación MFA → Panel.
2. Menú Apoyo a decisiones → Fuentes públicas → Laboratorio → detalle HLA → Abrir expediente completo.
3. Menú Apoyo a decisiones → Perfiles y vigencia → listado de perfiles.
4. Apoyo a decisiones → Crear análisis → Ruta regional estimada → completar grafo, origen y destino → guardar y consultar explicación.
5. Repetir Crear análisis para demanda/caducidad e inconsistencias. Mostrar límites e insuficiencia de datos si corresponde.
6. Inventario sanguíneo → buscar folio ficticio → Ver detalle → Abrir expediente completo → Liberación médica. Mostrar rechazo sin reautenticación y liberación académica autorizada por el perfil de prueba.
7. Cerrar sesión → médico receptor → Solicitudes → Registrar solicitud → guardar → abrir nuevo registro desde listado → Evaluar candidatos → perfil académico → evaluación → Registrar dictamen.
8. Cerrar sesión → médico origen → Laboratorio → resultado ficticio → Registrar corrección → abrir resultado nuevo → Revisar resultado. Se conserva el resultado previo.
9. Médico receptor → Solicitudes → detalle → evaluación histórica → Autorizar reserva → rechazo por obsolescencia → nueva evaluación y revisión.
10. Apoyo a decisiones → Crear análisis → evaluación explicable, comparación logística y propuesta de cobertura. Regresar a solicitud/evaluación → Autorizar reserva.
11. Coordinador → Traslados → Reservas y asignaciones → reserva nueva → Planear traslado.
12. Operador/transportista/receptor, con cambios de sesión visibles: Traslados → detalle → pasos de preparación, recolección, tránsito, entrega y aceptación. Mostrar bloqueo de custodia incompleta. No publicar posiciones GPS.
13. Médico receptor → Inventario → buscar folio → destino y corrección documental; Reportes privados → generar reporte de custodia → consultar y descargar.
14. Auditor → Bitácora. Recorrido por menús médicos, coordinación, administración y donante; consulta de módulos, no certificación de todos sus CRUD.
15. Cerrar sesión.

## Reglas de la toma

- Apertura inicial del sitio antes de grabar. Durante la toma, solo menús, botones, búsquedas y formularios; ninguna URL escrita.
- Clics, desplazamientos y teclas enviados a macOS mediante CGEvent; lectura del DOM solo para localizar y comprobar controles.
- Los diálogos de detalle se abren y luego se usa «Abrir expediente completo». Las confirmaciones se atienden en su diálogo.
- Los formularios con retorno al listado se siguen desde el nuevo registro del listado.
- Captura física AVFoundation con cursor, pantalla completa, 15 fps y resolución 1440×900 para limitar carga.
- Credenciales y MFA fuera del montaje mediante cortes; originales privados. Títulos antes de funcionalidades y textos sobre reglas visibles.
- GPS físico aplazado; ETA modelada no es tráfico medido, entrega ni autorización clínica.
- Una interrupción o fallo se conserva en el registro técnico; no se presenta como flujo completado.

## Complemento del montaje

Tras el recorrido de perfiles: registrar una muestra ficticia vacía; consultar completitud sin aprobación clínica; mostrar perfil académico y detalle HLA; cerrar sesión y recorrer la página pública. Se omiten consultas repetidas de módulos ya demostrados.
