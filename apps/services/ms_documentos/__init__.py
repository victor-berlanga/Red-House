"""Propietario de archivos privados, versiones documentales y exportaciones."""

from redhouse.app import base_app, complete_app

VERSION = "0.4.1"


def create_app(config=None):
    app = base_app("documentos", config)
    app.config["VERSION"] = VERSION
    from .documents import install, shipment_access
    from .files import register_files
    from .local_objects import install as local_objects
    from .reports import install as reports

    local_objects(app)
    register_files(app, shipment_access)
    install(app)
    reports(app)
    return complete_app(app)
