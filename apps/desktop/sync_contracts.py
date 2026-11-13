"""Sincroniza contratos de construcción; la consola no importa el backend."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / 'apps/services'
DESTINATION = Path(__file__).resolve().parent / 'redhouse_desktop/contracts'
OWNERS = {
    'identidad': 'ms_identidad_acceso',
    **{name: 'ms_' + name for name in (
        'alertas', 'auditoria', 'compatibilidad', 'custodia', 'documentos',
        'inventario', 'priorizacion_geografia', 'receptores', 'transporte',
    )},
}
SCHEMAS = {
    'ms_identidad_acceso': ('login', 'refresh', 'reauthenticate', 'user_role', 'user_state', 'device_create', 'device_revoke'),
    'ms_inventario': ('cold_reading_create', 'label_issue', 'reservation_create', 'resource_create'),
    'ms_compatibilidad': ('evaluation_create', 'evaluation_review', 'lab_result_create', 'lab_result_review', 'lab_sample_receive'),
    'ms_documentos': ('export_create',),
    'ms_receptores': ('request_create',),
    'ms_transporte': ('shipment_scan', 'shipment_transition'),
}


def sources():
    mapping = {name + '.json': SERVICES / owner / 'contracts/openapi.json' for name, owner in OWNERS.items()}
    for owner, names in SCHEMAS.items():
        mapping.update({name + '.xsd': SERVICES / owner / 'contracts' / (name + '.xsd') for name in names})
    mapping.update({
        'response.xsd': SERVICES / 'redhouse/response.xsd',
        'tracking_event.xsd': SERVICES / 'ms_transporte/contracts/websocket/event.xsd',
        'tracking_message.xsd': SERVICES / 'ms_transporte/contracts/websocket/message.xsd',
    })
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Falla si una copia difiere; no escribe archivos.')
    args = parser.parse_args()
    mapping = sources()
    missing = [str(path.relative_to(ROOT)) for path in mapping.values() if not path.is_file()]
    if missing:
        parser.exit(1, 'Faltan contratos propietarios: ' + ', '.join(missing) + '\n')
    existing = {path.name for path in DESTINATION.iterdir() if path.is_file()}
    unexpected = existing - set(mapping)
    if unexpected:
        parser.exit(1, 'Revisar contratos adicionales, no se eliminan: ' + ', '.join(sorted(unexpected)) + '\n')
    changed = []
    for name, source in sorted(mapping.items()):
        destination = DESTINATION / name
        content = source.read_bytes()
        if not destination.is_file() or destination.read_bytes() != content:
            changed.append(name)
            if not args.check:
                destination.write_bytes(content)
    if args.check and changed:
        parser.exit(1, 'Contratos fuera de sincronía: ' + ', '.join(changed) + '\n')
    print(f'{len(mapping)} contratos comprobados; {len(changed)} copias ' + ('diferentes.' if args.check else 'actualizadas.'))


if __name__ == '__main__':
    main()
