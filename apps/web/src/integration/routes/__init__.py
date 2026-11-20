"""Registro de módulos web; conserva los nombres de endpoint existentes."""

from .common import public, portal, regional, inventory, organs, admin, display
from . import (
    auth,
    dashboard,
    people,
    agenda,
    requests,
    logistics,
    tracking,
    administration,
    monitoring,
    audit,
    files,
    quality,
    decision_support,
    conservation,
    configuration,
    documents,
)

from .. import navigation

navigation.register(portal)

# El módulo inventory comparte nombre con el Blueprint: importar explícitamente.
from importlib import import_module

import_module(__name__ + ".inventory")
from .common import inventory


def blueprints():
    return public, portal, regional, inventory, organs, admin
