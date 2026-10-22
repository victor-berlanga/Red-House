"""Registro de módulos web; conserva los nombres de endpoint existentes."""

from .common import public, portal, regional, inventory, organs, admin, display
from . import (
    auth,
    dashboard,
    people,
    requests,
    logistics,
    administration,
    monitoring,
    audit,
    files,
)

# El módulo inventory comparte nombre con el Blueprint: importar explícitamente.
from importlib import import_module

import_module(__name__ + ".inventory")
from .common import inventory


def blueprints():
    return public, portal, regional, inventory, organs, admin
