"""Genera contratos revisables y apuntes TXT por servicio; no lee secretos."""

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redhouse.codec import request_xsd
from redhouse.config import SERVICES
from redhouse.examples import request_xml, sample
from redhouse.openapi import META, spec
from redhouse.output_schemas import result_schema

DESCRIPTIONS = {
    "identidad_acceso": (
        "Identidad y acceso",
        "Identifica a cada persona y limita qué puede hacer y en qué institución.",
        "Usuarios, instituciones, sesiones registradas y hashes scrypt en PostgreSQL. Redis conserva sesiones activas, permisos versionados, renovaciones y revocaciones.",
        "Un médico inicia sesión, recibe JWT y renovación; Inventario verifica su sesión y permisos antes de reservar.",
        "¿Por qué no basta JWT? Una firma válida no demuestra que la sesión siga activa: Redis permite revocar y cambiar permisos.\n¿Se acepta alg:none? No. Solo RS256 con emisor, audiencia y claims obligatorios.\n¿Qué pasa con una renovación reutilizada? Se revoca su familia de sesión.\n¿El administrador puede ver expedientes? No por tener ese rol.\n¿La contraseña es cifrada? Se conserva un hash scrypt; no se recupera la original.",
    ),
    "donantes": (
        "Donantes",
        "Gestiona registros preliminares, consentimiento, dictamen humano, donaciones, campañas y citas.",
        "PostgreSQL conserva expedientes y transacciones. Redis valida acceso y limita consumo. Outbox publica auditoría y avisos dirigidos al donante.",
        "Un donante se registra y agenda una cita. Un médico registra elegibilidad; después se documentan recolección y procesamiento.",
        "¿El sistema decide elegibilidad? No; requiere dictamen humano.\n¿Puede excederse el cupo? La campaña se bloquea y cuenta citas activas dentro de una transacción.\n¿Un donante consulta a otro? No: se exige su cuenta y ámbito.\n¿Cancelar una cita libera cupo? Sí.\n¿Órganos y sangre comparten reglas? No: la donación identifica el tipo; este registro no sustituye autorizaciones específicas de donación de órganos.",
    ),
    "receptores": (
        "Receptores y solicitudes",
        "Administra expedientes de receptores y el ciclo de vida y cobertura de solicitudes.",
        "PostgreSQL conserva receptores, solicitudes y retenciones de capacidad; Redis valida sesión y permisos. Auditoría/alertas reciben eventos durables.",
        "Una solicitud de una unidad retiene un cupo antes de que Inventario reserve el recurso. Dos peticiones concurrentes no pueden cubrir dos veces ese cupo.",
        "¿Por qué existe una retención? Evita que dos recursos distintos excedan la misma solicitud.\n¿Se libera automáticamente al vencer una petición HTTP? No: un timeout no demuestra que la operación haya fallado. Se consulta y recupera.\n¿Se cancela con retenciones pendientes? No; primero se resuelve la coordinación.\n¿Cuándo cierra? Al confirmar la recepción de toda la cantidad solicitada.\n¿Cerrar significa trasplante? No: significa recepción logística.",
    ),
    "inventario": (
        "Inventario y reservas",
        "Mantiene unidades de sangre y ofertas de órganos, su disponibilidad, reservas y ubicación institucional.",
        "PostgreSQL es autoridad de recursos, movimientos y operaciones. Redis ofrece caché breve de disponibilidad y seguridad; una reserva siempre reconsulta PostgreSQL.",
        "El origen registra y libera un recurso; el destino lo reserva con evaluación y dictamen favorable; tras recepción queda registrado en la institución de destino.",
        "¿Cómo evita doble reserva? Bloqueo de fila y un índice único de reserva activa.\n¿Una caché desactualizada puede asignar sangre? No: solo orienta búsquedas.\n¿Para qué Idempotency-Key? Permite repetir tras perder una respuesta sin duplicar la reserva; otra entrada con la misma clave produce conflicto.\n¿Se pueden cancelar recursos recolectados? No.\n¿Se calcula caducidad clínica? No: el límite se captura y debe provenir de una fuente autorizada.",
    ),
    "compatibilidad": (
        "Compatibilidad",
        "Genera candidatos explicables y conserva evaluaciones y dictámenes humanos.",
        "PostgreSQL conserva instantáneas, versiones, candidatos y revisión. Flask consulta propietarios por HTTP; Redis valida JWT y permisos.",
        "Para RBC se aplica el filtro ABO/RhD ya documentado. Para órgano se preselecciona mismo tipo y ABO idéntico, sin interpretar HLA.",
        "¿Una coincidencia es autorización clínica? No.\n¿Interpreta HLA? No; su interpretación corresponde al especialista.\n¿Qué sucede con datos faltantes? La evaluación conserva exclusiones logísticas y aviso de limitaciones.\n¿Se conserva la regla usada? Sí: RBC-1.0 u ORGAN-1.0 y versiones de datos/ruta.\n¿Puedo reservar solo con evaluación? No: también se exige dictamen favorable y confirmación humana.",
    ),
    "priorizacion_geografia": (
        "Priorización y geografía",
        "Mantiene estimaciones de rutas, ranking operativo y propuestas de cobertura máxima.",
        "PostgreSQL conserva rutas versionadas, factores, rankings y propuestas. Python ejecuta ordenamiento y matching bipartito Hopcroft–Karp. Redis aplica seguridad.",
        "Si un paciente admite A o B y otro solo A, un recorrido voraz puede dejar uno sin propuesta. Un camino aumentante permite proponer B al flexible y A al restringido.",
        "¿Por qué dos responsabilidades en un servicio? Ruta, tiempo y distancia participan en el ranking operativo; sus contratos permanecen separados.\n¿Usa Google Maps? No: las rutas actuales son estimaciones capturadas con procedencia.\n¿El ranking prioriza clínicamente? No: orden operativo ilustrativo, sin ponderaciones médicas inventadas.\n¿El algoritmo es no trivial? Matching utiliza BFS/DFS y caminos aumentantes; O(E raíz(V)) con las limitaciones documentadas.\n¿La propuesta reserva? No: reserva y autorización se realizan posteriormente en Inventario.",
    ),
    "transporte": (
        "Transporte",
        "Planea y sigue traslados, responsables, incidencias, ubicación autorizada y evidencias.",
        "PostgreSQL conserva órdenes, pasos y referencias de archivos. MongoDB recibe documentos y telemetría mediante outbox. Redis conserva sesión y referencia de ubicación reciente. GCS dispone de adaptador opcional para archivos privados.",
        "Coordinación planea; origen prepara; traslado recoge y entrega; destino acepta. Cada paso genera eventos de custodia y auditoría.",
        "¿Cualquiera actualiza una orden? No: rol, institución y responsable asignado.\n¿Se registra GPS permanentemente? No: solo responsable y estados COLLECTED/IN_TRANSIT.\n¿Una caída de custodia pierde una recolección? El evento queda durable en PostgreSQL y se reintenta.\n¿Se puede deshacer una recolección física? No; se registra la incidencia.\n¿GCS está comprobado en nube? No: el adaptador exige bucket y credenciales reales y devuelve 503 si faltan; no fabrica URLs.",
    ),
    "custodia": (
        "Cadena de custodia",
        "Conserva secuencia verificable de transferencias físicas y referencias de evidencia.",
        "PostgreSQL mantiene el registro autoritativo con secuencia e historial protegido. MongoDB recibe la proyección documental. SHA-256 enlaza eventos; Redis valida identidad y acceso.",
        "Transporte produce PLANNED, PREPARED, COLLECTED, IN_TRANSIT, DELIVERED y ACCEPTED; Custodia los incorpora sin duplicarlos ni admitir huecos.",
        "¿Por qué se separa de Transporte? La orden cambia; los eventos históricos deben conservarse.\n¿Se admite un evento fuera de orden? No: se reintenta después del anterior.\n¿El hash demuestra que la sangre fue entregada? No: detecta alteración del registro; no certifica por sí mismo la veracidad física.\n¿Ni el administrador de base puede alterarlo? La protección corresponde a credenciales de aplicación; un propietario de infraestructura requiere controles adicionales.\n¿Transportista ajeno puede consultar? No: se verifica la asignación mediante Transporte.",
    ),
    "alertas": (
        "Alertas",
        "Genera una bandeja de avisos por eventos y conserva su atención.",
        "PostgreSQL conserva alertas, destinatarios y acuses. Redis valida sesión y permisos. Eventos se deduplican por identificador.",
        "Una reserva avisa a las instituciones implicadas; una cita o evaluación de donante puede avisar a su cuenta específica.",
        "¿Se enviaron correos o push? No: este incremento implementa bandeja API persistente; proveedores externos son posteriores.\n¿Un evento repetido crea dos alertas? No.\n¿Puede ver avisos de otro hospital? No.\n¿Acusar recibo modifica la solicitud? No: solo el estado del aviso.\n¿Se incluyen estudios o contraseñas? No; códigos de mensaje y referencias minimizadas.",
    ),
    "auditoria": (
        "Auditoría",
        "Recibe registros minimizados de accesos, cambios, evaluaciones y decisiones.",
        "PostgreSQL mantiene registro inmutable bajo credenciales de aplicación. MongoDB proporciona proyección documental flexible. Redis controla sesión, perfil Auditor y región.",
        "El cambio y su evento se guardan juntos en el servicio de origen. Auditoría recibe después el evento con reintentos y deduplicación.",
        "¿Qué pasa si Auditoría cae? Los eventos quedan pendientes en cada outbox.\n¿Y si falla el registro local obligatorio? Se revierte la transacción local; una retención remota puede necesitar compensación.\n¿Almacena JWT o estudios? No.\n¿Es síncrona toda la auditoría? El registro local es transaccional; la centralización es eventual.\n¿Qué identifica un recorrido? X-Correlation-ID se propaga entre llamadas y eventos.",
    ),
    "monitoreo": (
        "Monitoreo",
        "Consulta salud y conserva disponibilidad, latencia, versión y dependencia que falla.",
        "HTTP requests consulta /health/ready; MongoDB guarda primero cada sondeo y PostgreSQL conserva las verificaciones. El estado puede consultarse desde MongoDB si PostgreSQL falla. Redis protege las consultas. El worker sondea cada 30 segundos.",
        "Con Redis detenido, el proceso sigue vivo, readiness se degrada y las operaciones protegidas fallan de forma cerrada.",
        "¿Liveness significa que todo funciona? No: solo que el proceso responde.\n¿Readiness revisa migración? Sí: comprueba versión de esquema y dependencias aplicables.\n¿Todos requieren MongoDB? No: su health indica not_applicable donde no corresponde.\n¿Storage está verde sin GCS? Se informa not_configured, required=false, no se simula disponibilidad.\n¿Hay una interfaz? El portal integrado consulta estados y verificaciones mediante la API con el JWT del usuario autorizado.",
    ),
}


def main():
    notes = ROOT.parents[1] / "stuff" / "presentacion"
    notes.mkdir(parents=True, exist_ok=True)
    index = [
        "RED HOUSE — APUNTES PARA PRESENTACIÓN",
        "Fecha: 2026-10-08",
        "",
        "Diez microservicios y un componente de monitoreo.",
        "Los puertos 5101–5111 son los valores por defecto; el entorno de prueba utiliza puertos libres y los registra en state.json.",
        "El portal Flask/Jinja2 ya consume las API de los servicios. Móvil, escritorio y contenedores siguen pendientes.",
        "Los apuntes deben leerse junto a documentation/markdowns/Pruebas_y_validacion.md para conocer exactamente qué se comprobó.",
        "",
    ]
    for number, (service, port) in enumerate(SERVICES.items(), 1):
        module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
        app = importlib.import_module(module).create_app(
            {
                "DATABASE_URL": "postgresql://UNCONFIGURED",
                "JWT_PUBLIC_KEY": "UNCONFIGURED",
                "JWT_PRIVATE_KEY": "UNCONFIGURED",
                "SERVICE_PRIVATE_KEY": "UNCONFIGURED",
            }
        )
        title, purpose, data, scenario, questions = DESCRIPTIONS[service]
        folder = ROOT / module
        contracts = folder / "contracts"
        contracts.mkdir(exist_ok=True)
        (contracts / "openapi.json").write_text(
            json.dumps(spec(app), indent=2, ensure_ascii=False) + "\n"
        )
        # Las migraciones autoritativas viven únicamente en migrations/.
        (contracts / "migration-001.sql").unlink(missing_ok=True)
        for c in app.extensions["contracts"]:
            response = {
                "type": "object",
                "required": ["data", "meta"],
                "properties": {
                    "meta": META,
                    "data": c["result"] or result_schema(service, c["name"]),
                },
            }
            (contracts / (c["name"] + ".response.json")).write_text(
                json.dumps(response, indent=2, ensure_ascii=False) + "\n"
            )
            if c["model"]:
                (contracts / (c["name"] + ".xsd")).write_bytes(request_xsd(c["model"]))
                value = sample(c["model"].model_json_schema())
                (contracts / (c["name"] + ".example.json")).write_text(
                    json.dumps(value, indent=2, ensure_ascii=False) + "\n"
                )
                (contracts / (c["name"] + ".example.xml")).write_text(
                    request_xml(value) + "\n"
                )
        filename = f"{number:02d}-{module}.txt"
        endpoints = "\n".join(
            f"  {c['method']} {c['path']}: {c['summary']}"
            for c in app.extensions["contracts"]
        )
        text = f"""RED HOUSE — {title.upper()}
Unidad: {module}
Puerto por defecto: {port}
Versión del servicio: {app.config["VERSION"]}

1. QUÉ HACE Y POR QUÉ EXISTE
{purpose}

2. TECNOLOGÍAS Y DATOS
Flask (REST), Python 3.12+, Psycopg, PostgreSQL, PyJWT/cryptography (RS256), Redis, Pydantic, lxml (XML/XSD), Waitress, Swagger/OpenAPI.
{data}
Entre servicios se utilizan firmas Ed25519, nonce con expiración, autorización delegada donde aplica e identificadores de correlación.

3. ESCENARIO PARA EXPLICARLO
{scenario}

4. CONTRATOS Y OPERACIONES
API v1; JSON para móvil y XML para escritorio. Swagger local en /docs y OpenAPI en /openapi.json.
Entradas XML con raíz request y XSD por operación. Respuestas XML conservan tipos mediante field/item y atributo type.
{endpoints}

5. SEGURIDAD Y ERRORES
Acceso denegado por defecto. JWT con firma, emisor, audiencia, expiración, sesión, revocación y permisos vigentes.
Validación estricta: campos desconocidos, nulos no autorizados, cadenas vacías, tipos incorrectos, JSON duplicado, NaN/Infinity y XML con DTD se rechazan.
Errores equivalentes JSON/XML: 400/422 entrada, 401 autenticación, 403 autorización, 404 inexistente, 409 estado/versión, 429 límite, 503 dependencia.
No se exponen credenciales ni contenido clínico en logs; cada petición registra ruta, estado, duración y correlación.

6. PREGUNTAS QUE PODRÍAN HACER
{questions}

7. GUION BREVE PARA UNA DIAPOSITIVA
Problema: {purpose}
Entrada: petición REST autorizada y validada.
Proceso: aplicar permisos, reglas operativas y persistencia propia.
Salida: resultado JSON/XML, correlación y evento auditable cuando corresponde.
Presentación: Swagger -> operación -> consulta posterior -> revisión de auditoría/salud.

8. CÓMO COMPROBAR Y QUÉ NO AFIRMAR
Leer apps/services/README.md y documentation/markdowns/Pruebas_y_validacion.md.
Cada unidad conserva sus consultas, contratos outputs.json y migraciones. scripts/package_service.py entrega un solo dominio con una copia de utilidades comunes; scripts/upgrade.py y local.py restart-service permiten actualizarlo individualmente.
XML de salida se valida con XSD estructural y DTO semántico: redhouse.xml_response.validate_response.
El estado /health/worker permite detectar workers detenidos o publicación de eventos atrasada. Los motivos se conservan en el historial privado del propietario; los eventos centrales son minimizados.
Las reglas no sustituyen evaluación clínica. No afirmar despliegue en GCP, Docker, HLA automatizada o móvil/escritorio integrados.
No mostrar state.json, archivos de configuración privada ni tokens durante la presentación.
La web integrada tiene pruebas HTTP con dependencias reales y recorridos de navegador. Leer apps/web/README.md.
"""
        (notes / filename).write_text(text)
        index.append(f"{filename}: {title}")
        (folder / "README.md").write_text(
            f"# {title}\n\n{purpose}\n\nPuerto por defecto: `{port}`.\n\nEjecutar desde `apps/services`: `python run.py {service} --config /ruta/privada/{service}.json`.\n\nSwagger: `/docs`. Contratos estáticos y XSD: [contracts](contracts). Guía común: [README](../README.md).\n\nApuntes de presentación: [TXT](../../../stuff/presentacion/{filename}).\n"
        )
        (folder / "requirements.txt").write_text("-r ../requirements.txt\n")
        env_lines = [
            "# Configuración exclusiva de esta unidad; guardar fuera de Git.",
            f"{service.upper()}_DATABASE_URL=postgresql://USUARIO:CAMBIAR@127.0.0.1:5432/red_house?options=-csearch_path%3Daccess_{service}%2Cpg_catalog",
            f"REDIS_URL=redis://{service}:CAMBIAR@127.0.0.1:6379/0",
            "REDIS_PREFIX=redhouse-ms:",
            "JWT_PUBLIC_KEY=PEM_PUBLICO_RS256",
            f"{service.upper()}_SERVICE_PRIVATE_KEY=PEM_PRIVADO_ED25519_EXCLUSIVO",
            "SERVICE_PUBLIC_KEYS={}",
            "SERVICE_URLS={}",
        ]
        if service == "identidad_acceso":
            env_lines.append("JWT_PRIVATE_KEY=PEM_PRIVADO_RS256_SOLO_IDENTIDAD")
        if service in {"transporte", "custodia", "auditoria", "monitoreo"}:
            env_lines.append(
                f"{service.upper()}_MONGODB_URL=mongodb://{service}:CAMBIAR@127.0.0.1:27017/rh_{service}?authSource=rh_{service}"
            )
        if service == "transporte":
            env_lines.append("GCS_BUCKET=")
        (folder / ".env.example").write_text("\n".join(env_lines) + "\n")
        (folder / "run.py").write_text(
            f'from pathlib import Path\nimport sys\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nfrom run import main\n\nif __name__ == "__main__":\n    sys.argv.insert(1, "{service}")\n    main()\n'
        )
    (notes / "00-LEER-PRIMERO.txt").write_text("\n".join(index) + "\n")
    print(
        "Contratos, once apuntes TXT e índice generados sin leer configuración privada."
    )


if __name__ == "__main__":
    main()
