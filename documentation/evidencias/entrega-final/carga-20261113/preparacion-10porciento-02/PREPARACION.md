# Preparación del segundo intento aislado al 10 %

El primer intento y sus 48.200 eventos confirmados permanecen en [su evidencia](../intento-10porciento-01/RESULTADOS.md); no se reutilizará ni borrará su laboratorio. La corrección vuelve a recorrer el censo de disco hasta tres veces ante una desaparición concurrente y falla cerrado si no obtiene un censo estable. Se aprobaron 18 pruebas ligeras del módulo, incluidas desaparición transitoria/persistente y raíz ausente o simbólica.

Las [huellas del incremento](fuentes.sha256) y el [manifiesto de 942 archivos de servicios](fuentes-services.json) se capturaron antes de la nueva corrida, incluidas las fuentes I06 presentes. Se comprobarán otra vez antes y después; no se ha iniciado un nuevo laboratorio.

Comando desde la raíz del repositorio, solo durante la ventana coordinada:

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --scale-percent 10 --seed 20261113 --mongod "$PWD/.local/tools/mongodb-8.0.17/bin/mongod" --sustained-read
```

El entorno será nuevo y privado. Las guardas permanecen en al menos 3 GiB libres y hasta 1,5 GiB propios; no se reduce el umbral si falta espacio. La lectura sostenida exige MFA, seis usuarios, calentamiento y medición separados, y revocación verificada. Se conservará cualquier fallo de este intento por separado; no se han obtenido resultados ni se ha medido la duración total.
