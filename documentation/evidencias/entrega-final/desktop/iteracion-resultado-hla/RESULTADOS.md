# Resultado HLA: formularios y contratos sintéticos

El incremento permite documentar un resultado pendiente o informado, corregir un resultado con antecedente fijo, declarar HLA por locus, registrar emisión y seleccionar un documento ya verificado del antecedente. La revisión muestra la declaración y el documento. Un conflicto o respuesta incierta conserva los datos en una vista bloqueada; no inicia automáticamente otra operación. Un rechazo de validación reconocido del primer envío permite corrección humana. Las confirmaciones y los callbacks quedan ligados al contexto de sesión.

**Alcance: pruebas con dobles; no se ejecutaron API ni laboratorio real para este incremento.** El selector no carga archivos: DESK-04 documental sigue parcial. El resultado sintético HLA no constituye interpretación ni autorización clínica.

- `unit-01`: 7/7 comprobaciones puras de XSD, documento ajeno/no verificado y correlación de respuestas.
- `qt-01`: 18/18 pruebas Qt con dobles, incluidos callbacks reales de `secure_command` y reautenticación, 422/412, cambio de SID y antecedente fijo. Capturas con tema Qt genérico; preceden al ajuste de encabezados y contraste.
- `qt-02`: 2/2 controles visuales posteriores al ajuste, con tema Qt genérico. El modelo propietario `ResultCreate` confirmó sin servicio que conserva los loci suministrados, normaliza catálogo omitido a `None` y admite emisión en `PENDING`.
- `qt-03`: 3/3 comprobaciones de los estados con la hoja de estilo real del producto. Dirección inspeccionó la vista superior y el estado bloqueado.
- `qt-04`: 1/1; captura desplazada al final del formulario con estilo real, inspeccionada para emisión, documento y nota completa. Solo cambia el momento del desplazamiento del arnés; no repite escritura real.

Cada directorio conserva JUnit y salida; las capturas son datos sintéticos. Los XML publicados solo normalizan espacios finales; originales y fuentes privadas del candidato permanecen en `.local/artifacts/desktop/resultado-hla-candidato-20261116/`. `fuentes.sha256` identifica los archivos integrados. Los totales se informan por ejecución y no se suman como pruebas independientes. No acredita persistencia real, ClamAV, GCS, impresión ni Windows.

Después de integrar y cotejar las tres fuentes y el test byte a byte, la regresión de contexto de sesión, formularios y renovación aprobó **31/31 en 2,26 s**, sin motores. [JUnit integrado](regresion-contextos-integrada.xml). No se repitieron las 18 pruebas idénticas del candidato. El primer `git apply --check` omitió `-p0` y falló sin mutaciones; con el nivel correcto de rutas se integró el mismo parche.
