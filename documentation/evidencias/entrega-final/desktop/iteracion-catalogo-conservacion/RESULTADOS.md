# Catálogo de conservación en escritorio — 16/11/2026

Inventario incorpora consulta paginada y detalle de equipos y perfiles térmicos por XML/XSD. OPERATOR registra equipos; MEDICAL registra o corrige perfiles académicos con valores, fuente y fecha confirmados expresamente. No hay temperaturas predeterminadas ni habilitación clínica. La vinculación exige unidad propia en estado permitido, equipo activo y perfil compatible; conserva el perfil de laboratorio.

Los comandos usan diario cifrado, reautenticación cuando corresponda y recuperación con la misma clave y cuerpo. Antes de cerrar el pendiente se comprueban institución, autor cuando lo contiene el contrato, datos y fecha. Las consultas y formularios mantienen el contexto de sesión; se rechazan controles pertenecientes a otra unidad.

[Diez pruebas nuevas](unit.xml) aprobaron en 2,55 s sobre el candidato: respuesta perdida y recuperación de ambas altas, institución ajena, rechazo de perfil no sintético, permisos/navegación/paginación, controles ajenos, conservación del perfil de laboratorio, cambio de sesión y antecedente actualizado. Usan Qt, diario y XSD reales con transporte simulado. No prueban persistencia remota ni funcionamiento clínico.

Las 57 copias XSD coincidieron con sus propietarios y los ocho archivos integrados fueron idénticos al candidato probado. Después se corrigió únicamente el crecimiento horizontal de campos de receptor y planificación, motivado por capturas nativas anteriores. [Huellas y separación del alcance](fuentes.json). No se repitieron las diez pruebas por esas dos propiedades de presentación.

Pendientes de este corte: recorrido Qt/XML contra el servidor, inspección visual de los formularios nuevos y del ajuste de ancho, y empaquetado final. DESK-10 y etapa05 continúan parciales.
