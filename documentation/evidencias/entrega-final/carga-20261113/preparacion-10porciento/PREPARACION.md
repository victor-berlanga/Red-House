# Preparación del ensayo aislado al 10 %

Código revisado y congelado para el primer intento; no se ha ejecutado la preparación al 10 % ni la lectura sostenida. Las [huellas de los archivos del incremento](fuentes.sha256) son anteriores al ensayo. El propio arnés también registra huellas del conjunto de fuentes y configuraciones antes y después.

Comando desde la raíz del repositorio, únicamente en la ventana coordinada:

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --scale-percent 10 --seed 20261113 --mongod "$PWD/.local/tools/mongodb-8.0.17/bin/mongod" --sustained-read
```

El comando crea un directorio privado nuevo en `/tmp`, conserva allí el primer informe y diagnóstico si falla, y detiene sus procesos al finalizar. Requiere al menos 3 GiB libres y limita el tamaño lógico propio a 1,5 GiB; verifica las guardas por lote y durante Locust. Rechaza variables heredadas de conexión o credenciales de nube indicadas en el código. No acepta un destino ni base preexistente.

La carga sostenida emplea seis identidades, MFA para los perfiles obligados, al menos 30 segundos de calentamiento tras sus seis inicios y 120 segundos de medición, seguidos de drenado y revocación verificada. Se requieren al menos 150 segundos solo para esos dos periodos; el tiempo total de inicialización, 100.000 inserciones, enrolamiento, verificaciones y cierre aún no está medido. Los datos y el resultado de carga se informan por separado. Una falla de configuración o autenticación invalida la fase; no se elevarán cuotas ni se omitirá MFA para hacerla pasar.

Las 41 pruebas ligeras de preparación, corte de métricas, cliente y limpieza pasaron antes de este ensayo; emplean dobles y no constituyen evidencia de funcionamiento de la nueva topología con motores reales.
