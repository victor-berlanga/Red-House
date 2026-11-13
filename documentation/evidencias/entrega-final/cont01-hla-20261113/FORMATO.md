# Formato posterior de pruebas

Tras las ejecuciones originales, se aplicó `ruff format` a las pruebas listadas. Los manifiestos SHA y JUnit históricos no se modificaron. Se comparó `ast.dump(ast.parse(...), include_attributes=False)` antes y después, y la huella SHA-256 del AST coincidió para cada archivo. Esto acredita equivalencia estructural de Python para el cambio de formato; no vuelve a ejecutar las pruebas ni sustituye sus fuentes históricas.

| Archivo | SHA-256 antes | SHA-256 después | SHA-256 AST común |
| --- | --- | --- | --- |
| `test_storage_recovery.py` | `c9f7b6512801596000b8d96f39105fb0af65316a8bd5b359e3c964e3a47ef49a` | `ee22d2de720cc1b97e131f54981096cb3e2bc2904c18a3a36504a8cb56f45c05` | `f5a2610e6b2ac33786bd758e971af04231e7190ba6a0300ea9749104938dfa25` |
| `test_cont01_hla_evaluation.py` | `6a7d62ca81e3f0b9cb98b98a575dabd1a3d9bbe89a9347f6ffc06ced1b36ecd6` | `7ccb2b29d557131d7e683086c4a64483c3f37f1caeae61f7e91b989ef3789783` | `de2d64c10acc06cd2ea2e09eb5790b6c6b91129a55f759e9628b43b19efd6d9d` |

La prueba documental aún no se ha ejecutado. La comparación AST de este informe cubre los dos archivos indicados.
