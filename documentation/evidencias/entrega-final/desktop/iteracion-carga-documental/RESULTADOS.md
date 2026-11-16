# Carga documental desde resultados

El incremento prepara un documento para el resultado seleccionado, transfiere el archivo a la URL autorizada y consulta su verificación. El diario conserva la intención, identificador y huella, sin ruta, URL temporal, contenido ni credenciales. La recuperación de `MISSING` reutiliza el documento y la clave; necesita volver a elegir un archivo con la misma huella. La verificación de una transferencia incierta no pide el archivo.

## Evidencia local

- Pruebas sin servicios: 9/9, 4/4, 4/4 y 3/3 en ejecuciones separadas (`unit-02` a `unit-05` del expediente privado). Cubren, entre otros, origen y cabeceras, clave estable, respuestas 201/412 simuladas, aislamiento del diario y cambio de sesión durante carga o verificación. No acreditan almacenamiento real ni inmutabilidad del servidor.
- Qt con dobles: 2/2 (`qt-02`), incluyendo cancelación y cambio de sesión; 1/1 adicional (`qt-03`) para la presentación tras añadir el botón Cancelar. El test ya integrado se ejecutó 1/1 adicionalmente tras ajustar su destino temporal de captura. La captura [formulario-doble.png](formulario-doble.png) utiliza el estilo de la aplicación. Dirección la inspeccionó: campos y acciones legibles.
- Prueba Qt posterior 2/2 (`qt-callback-01`): conserva el mensaje al verificar desde resultados, actualiza pendientes y oculta las dos acciones al cambiar de área.
- `document_prepare.xsd` coincide byte a byte con su propietario. Las fuentes candidatas compilaron con Python.
- Primer intento de pruebas puras: 8/9, por expectativa incompleta de una excepción del propio doble; se corrigió y se conserva separado. Primer intento visual: fallo al cerrar un cliente doble que carecía del atributo `access`; se corrigió el doble. No son pruebas reales del servidor.

Los JUnit públicos omiten `hostname` y se han normalizado como XML. [HUELLAS.txt](HUELLAS.txt) conserva SHA-256 de cada original privado y copia pública; cada archivo conserva el nombre de su ejecución.

## Pendiente

Confirmar con fixture real, `TESTING=False`, XML, CA verificada y ClamAV real la secuencia PENDING → documento CLEAN → corrección HLA → revisión médica. Probar por separado el reintento LOCAL `MISSING` y su inmutabilidad bajo el parche del propietario. El recorrido real no se ha ejecutado; tampoco acredita GCS ni operación clínica.

Huellas de preparación: parche privado `cdff334f6c9ae32cb684090a86c6582a6446591312370537f3fcf3faf683c17d`; captura `34f5103bcc5a87caf22c36cdb47f99f42a5028c9b2b9f1cc2e582be71f78f295`. La integración de raíz conservó bytes de producto; el test integrado guarda su captura en un directorio temporal en lugar de la ruta privada de preparación.
