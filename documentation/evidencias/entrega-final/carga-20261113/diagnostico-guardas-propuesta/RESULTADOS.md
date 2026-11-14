# Diagnóstico propuesto para guardas de carga

La revisión clasifica los límites de espacio con códigos fijos y conserva los valores y umbrales medidos. Para un fallo de censo o del sistema de archivos conserva únicamente categoría, clase permitida y, cuando corresponde, errno de una lista fija. Cada muestra y cada interrupción registrada incluyen UTC y tiempo transcurrido. No copia mensajes, rutas ni credenciales al resumen; no cambia límites ni plazos. Esta revisión no determina retrospectivamente el motivo no registrado del [segundo intento](../intento-10porciento-02/RESULTADOS.md).

La primera ejecución selectiva de pruebas obtuvo 30 aprobadas y una fallida: el test directo del controlador importó Locust tras `ssl`, provocando una recursión de monkey-patch de gevent. Se ajustó únicamente ese test simulado para establecer `LOCUST_SKIP_MONKEY_PATCH=1`; no se cambia la configuración de la ejecución real. La repetición siguiente pasó 32/32:

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/pytest -q apps/services/tests/test_load_pilot_unit.py apps/services/tests/test_sustained_read_unit.py
```

Las pruebas cubren señal de interrupción para límites y fallos de censo, sanitización y límites, además de marcas de tiempo. Utilizan dobles; esta revisión aún no se ha ensayado con motores reales. No hay un JUnit archivado de esas dos ejecuciones; el fallo y el resultado se conservan aquí sin atribuirles otra evidencia.
