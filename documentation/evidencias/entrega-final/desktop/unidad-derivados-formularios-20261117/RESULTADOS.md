# Legibilidad de alta de unidad y fraccionamiento

Aplicado el candidato visual revisado el 17 de noviembre de 2026. El formulario de alta amplía los campos y muestra la referencia UUID completa; calcula la altura de la procedencia según su texto y ancho, y ajusta el diálogo al seleccionar o quitar la donación. En fraccionamiento, los campos de cada derivado y el motivo utilizan el ancho disponible.

Validación previa con Qt real y datos sintéticos: tres capturas abiertas e inspeccionadas muestran UUID completo, procedencia en dos líneas sin recorte y motivo completo; ambas ventanas se cancelaron, sin llamadas a backend ni escrituras de negocio. [Capturas](capturas): alta de unidad y dos vistas de derivados. Los bytes integrados coinciden exactamente con los candidatos validados; [HASHES.json](HASHES.json) registra las huellas. No se repitieron pruebas de negocio ni la ejecución Qt Android C para este ajuste visual.

El resultado funcional anterior permanece en [Android C Qt/XML](../e2ec-android-20261117/RESULTADOS.md), con sus capturas originales y límites visuales históricos. Estas nuevas imágenes proceden de formularios sintéticos cancelados y no sustituyen aquellas capturas ni representan nuevas unidades o derivados persistidos.
