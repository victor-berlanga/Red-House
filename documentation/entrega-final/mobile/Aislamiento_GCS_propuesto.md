# Aislamiento propuesto para comprobar evidencia móvil

Estado: **propuesta, sin autorización de escritura ni borrado**. No se han creado recursos facturables, modificado IAM, arrancado VM, cambiado producción ni escrito objetos.

Consulta del 09/11/2026: el bucket `red-house-evidencias-sistemas-integracion-01` existe en US-CENTRAL1, clase STANDARD, prevención de acceso público `enforced` y acceso uniforme habilitado. Metadatos conservados en `documentation/evidencias/entrega-final/mobile/continuacion-20261109/gcs-metadatos-solo-lectura.json`. Existe un archivo ADC local; su presencia no demuestra autorización de firma ni permisos de objetos. No se imprimieron credenciales.

## Ensayo propuesto antes de usar el bucket

1. Mantener Identidad, Transporte, Documentos, PostgreSQL, Redis y MongoDB en el laboratorio temporal local. No reutilizar cuentas, traslados ni bases productivos.
2. Obtener del laboratorio una región y un traslado UUID exclusivos. El propietario Documentos usa `evidence/<región_uuid>/<traslado_uuid>/<objeto_uuid>`. Registrar previamente los dos UUID y cada objeto creado en un manifiesto privado de ensayo. No usar prefijos de regiones productivas.
3. Aprobar un máximo de cinco JPEG sintéticos, cada uno de hasta 10 MiB, sin personas ni datos clínicos. Validar hash, tamaño, MIME, generación exacta, carga firmada y rechazo de lectura anónima. El acceso firmado dura cinco minutos; no supone revocación inmediata en GCS.
4. Usar una identidad autorizada para ese prefijo, con lectura/creación y firma de URL. Preferir IAM condicional administrado por el responsable del bucket; cualquier modificación IAM necesita autorización aparte. No copiar claves privadas al repositorio ni al móvil.
5. Configurar ClamAV real y actualizado en el laboratorio antes de afirmar análisis limpio. No sustituir su resultado con una respuesta simulada. No enviar EICAR ni ensayar caídas de recursos habituales dentro de esta autorización propuesta.
6. Borrar exclusivamente los objetos del manifiesto, comprobando su generación exacta, si el usuario también autoriza esa limpieza. Si no autoriza borrado, entregar el manifiesto al responsable. No configurar lifecycle ni retención del bucket durante el ensayo.

## Requisitos aún por preparar

- Autorización explícita de creación y, separadamente, limpieza de esos objetos de prueba.
- Identidad con firma y permisos comprobables para el prefijo aislado; no basta el nombre del bucket.
- ClamAV/ClamD real disponible, configuración del servicio Documentos del laboratorio y endpoint de análisis sin exposición pública.
- Si no puede garantizarse aislamiento por prefijo, el responsable puede proporcionar un bucket de pruebas ya existente. Crear un bucket nuevo requiere autorización específica y no forma parte de las acciones ejecutadas.

Esta propuesta no bloquea la captura/preview local, cálculo SHA-256, adaptación JSON, manejo de errores ni las pruebas Android independientes de GCS.
