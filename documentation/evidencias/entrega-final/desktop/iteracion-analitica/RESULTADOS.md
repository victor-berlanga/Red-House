# Indicadores nativos Qt/XML

La consulta real posterior pasó con `operator2` y respuestas XML de Inventario, Receptores y Transporte; se compararon las tablas con los DTO y se cerró la familia propia. El primer intento falló por un campo opcional omitido y se conserva por separado. Los apartados siguientes distinguen los dobles previos, la corrección y la repetición real.

## Preparación con dobles

El candidato consulta las proyecciones XML `portal_metrics` de Inventario, Receptores y Transporte para un periodo elegido en hora local y enviado en UTC. Muestra tablas y barras nativas para inventario, solicitudes y caducidades, y la media observada de recolección a aceptación con su unidad. Conserva ámbito, población, base y periodo informados por cada propietario. Coordinación no solicita métricas de Receptores, cuyo contrato no autoriza ese rol; Transporte ve solo sus propios indicadores. No se añaden reglas clínicas ni se sustituyen valores ausentes por cero.

Cuatro pruebas con dobles pasaron en 0,90 s: población/ámbito y valor ausente, permisos por rol, cambio de sesión tras el selector y fallo parcial. El [JUnit saneado](junit-01.xml) omite el hostname. El ajuste visual posterior de la media no repitió esas pruebas.

Las vistas Cocoa con datos sintéticos muestran [gráficas y tabla superiores](indicadores-superior.png), [vista inferior anterior](indicadores-inferior.png), [servicios degradados](indicadores-degradado.png) y [periodo sin datos](indicadores-vacio.png). Dirección inspeccionó estas cuatro vistas. En la vista inferior anterior, una única media aparecía como barra completa; se sustituyó por una cifra con unidad y tabla, mostrada en la [captura final](indicadores-inferior-final.png), inspeccionada por quien preparó el cambio. El foco de Tab llegó a controles visibles y Page Down desplazó el panel ([resultado](teclado-scroll.json)); no acredita accesibilidad completa.

El cliente XML rechaza números no finitos antes de esta vista. El contexto conserva la cuenta, institución, rol y sesión durante la consulta. Estas capturas anteriores usan dobles; no representan datos del servicio ni validación clínica.

El candidato final tiene SHA-256: `app.py` `4fec67366ad6adff44d1d8f60406d97de3b2a49139bbac5a36eb2e3c45be201f`, `analytics.py` `f57dd3cc50712fc4ea0ce5806f79a468c6f08eb281b36a4c1ac8d88177eafa0d`, prueba `d67ed98049b711b3ace326ac3176f6e4707cde420c71e1ca3ab098622018e74d` y diff `8d16a9fa057aed87af5bfa3883fee0bebeffe2d8b925a13972bf69ef3cf11d1e`. La huella del JUnit privado original es `2061769cb0958a2fdc6336a91b2d9ee1da1018fda5506286711e737aabb82071`.

Posteriormente dirección integró `app.py`, `analytics.py` y la prueba con los hashes del candidato indicados arriba. La integración no convierte los dobles en prueba de servicio. La consulta real posterior se documenta a continuación; el paquete actualizado sigue pendiente.

## Consulta real y corrección

El primer intento Qt/XML terminó con salida 1: una respuesta válida omitió `unit`, campo opcional cuyo valor predeterminado contractual es `registros`. La interfaz lanzó `KeyError`; la familia propia quedó cerrada y las fuentes no cambiaron. Se conserva el [recibo saneado](real-01/receipt-saneado.json) y la [captura previa al fallo](real-01/01-periodo.png). No hubo escrituras de negocio.

Se corrigió la normalización de `unit` y `values` omitidos según el contrato. La regresión nueva pasó 1/1 en 1,71 s; la regresión de ventana/resumen pasó 1/1 en 4,52 s. Los [JUnit saneados](contract-defaults.xml) y [de ventana](integration-summary.xml) omiten el hostname. Las cuatro pruebas previas no se repitieron.

La repetición Qt/XML terminó con salida 0 usando `operator2`: consultó únicamente Inventario, Receptores y Transporte. El arnés comparó las tablas formateadas con las respuestas XML, incluidos la serie de caducidad vacía y el promedio de tiempos. Los [datos agregados saneados](real-02/payload-saneado.json), [recibo](real-02/receipt-saneado.json) y capturas de [periodo](real-02/01-periodo.png), [panel superior](real-02/02-superior.png) e [inferior](real-02/03-inferior.png) corresponden a esa ejecución. Dirección inspeccionó ambas vistas del panel. Se cerró la única familia propia y los manifiestos de fuentes antes/después coincidieron. Los valores visibles usan el formato numérico de la interfaz; el DTO conserva su precisión.

El fixture fue sintético y ACADEMIC. Los demás roles se cubrieron con dobles, no con esa ejecución real. No acredita Windows, paquete actualizado ni uso clínico. SQL/Redis se consultaron solo por el arnés para cierre de sesión; el cliente usó XML por HTTPS.

Huellas finales: `app.py` `4fec67366ad6adff44d1d8f60406d97de3b2a49139bbac5a36eb2e3c45be201f`, `analytics.py` `8426877f696a929634c4b4dcffb7387980083d0c4be0a1a35c399b8b58de0c0c`, prueba `dba6a1756cbed909ef872e3c75978379c86958e5dc6c2a51bfae6b7e95320ed7`. Ambos manifiestos de la repetición tienen SHA-256 `426db1041371b21d8f08fd3990db222eebfd778c7800c8ca7aa3bbedcb601d6a`. Los JUnit privados originales de campos opcionales y ventana tienen respectivamente SHA-256 `29719698bfde3e97dd87d296be5908aa53fd6c61c6cc365928b856a9c1629a32` y `a7d573ca8a5374e1baaed40ba63c9867ba915242decb7686dbdec68762f93979`.
