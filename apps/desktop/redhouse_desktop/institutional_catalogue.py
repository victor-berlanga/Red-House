"""Formularios institucionales XML; devuelven datos, nunca escriben en servidor.

La ventana integra COMMANDS/PATCH_OPERATIONS/SCHEMAS con su diario existente y
ejecuta secure_command después de aceptar el formulario. No hay registro global
en importación ni importaciones del backend.
"""

from uuid import UUID

from .client import ContractError

COMMANDS = {
    "sites_create": (
        "identidad-acceso",
        "/api/v1/catalogues/sites",
        "sites_create.xsd",
        False,
    ),
    "sites_edit": (
        "identidad-acceso",
        "/api/v1/catalogues/sites/{id}",
        "sites_edit.xsd",
        True,
    ),
    "capacities_create": (
        "identidad-acceso",
        "/api/v1/catalogues/capacities",
        "capacities_create.xsd",
        False,
    ),
    "capacities_edit": (
        "identidad-acceso",
        "/api/v1/catalogues/capacities/{id}",
        "capacities_edit.xsd",
        True,
    ),
}
PATCH_OPERATIONS = frozenset(("sites_edit", "capacities_edit"))
SCHEMAS = {"ms_identidad_acceso": tuple(COMMANDS)}
FIELDS = {
    "sites": ("name", "municipality", "address"),
    "capacities": ("name", "parent_id", "component", "quantity"),
}


def canonical_id(value):
    try:
        if not isinstance(value, str) or str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Selecciona un registro válido.") from exc
    return value


def catalogue_body(kind, values, item=None):
    """Valida campos de presentación; versión/relación se conservan al corregir."""
    if kind not in FIELDS:
        raise ValueError("Catálogo no disponible.")
    if not isinstance(values, dict) or (
        item is not None and not isinstance(item, dict)
    ):
        raise ValueError("Datos del formulario no válidos.")
    allowed = set(FIELDS[kind]) | (
        {"active", "reason", "human_confirmation"} if item is not None else set()
    )
    if set(values) != allowed:
        raise ValueError("Completa únicamente los campos del formulario.")
    result = {}
    for name in FIELDS[kind]:
        value = values[name]
        if name == "quantity":
            if type(value) is not int or not 0 <= value <= 100000:
                raise ValueError("La cantidad debe estar entre 0 y 100000.")
        elif name == "parent_id":
            value = canonical_id(value)
        else:
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 200:
                raise ValueError("Completa los textos con un máximo de 200 caracteres.")
            value = value.strip()
        result[name] = value
    if item is not None:
        canonical_id(item.get("id"))
        if (
            item.get("kind") != kind
            or type(item.get("version")) is not int
            or item["version"] < 1
        ):
            raise ValueError("Vuelve a consultar la versión del registro.")
        if kind == "capacities" and result["parent_id"] != item.get("parent_id"):
            raise ValueError("La sede de una capacidad existente no se cambia.")
        reason = values["reason"]
        if not isinstance(reason, str) or not 6 <= len(reason.strip()) <= 1000:
            raise ValueError("Escribe un motivo de entre 6 y 1000 caracteres.")
        if (
            type(values["active"]) is not bool
            or values["human_confirmation"] is not True
        ):
            raise ValueError("Revisa el estado y confirma la corrección.")
        result.update(
            active=values["active"],
            version=item["version"],
            reason=reason.strip(),
            human_confirmation=True,
        )
    return result


def validate_catalogue_item(kind, item, tenant_id):
    """Comprueba forma y ámbito de una fila antes de presentarla para edición."""
    try:
        canonical_id(tenant_id)
        canonical_id(item["id"])
        if item["kind"] != kind or item["tenant_id"] != tenant_id:
            raise ValueError()
        if (
            type(item["version"]) is not int
            or item["version"] < 1
            or type(item["active"]) is not bool
        ):
            raise ValueError()
        catalogue_body(kind, {key: item[key] for key in FIELDS[kind]})
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ContractError(
            "El registro institucional no está disponible para esta consulta."
        ) from exc
    return item


def validate_catalogue_result(operation, identifier, body, result, tenant_id):
    """Correlaciona antes de que el integrador marque COMPLETED en el diario."""
    if operation not in COMMANDS:
        raise ContractError("Operación institucional desconocida.")
    kind = operation.rsplit("_", 1)[0]
    try:
        canonical_id(tenant_id)
        canonical_id(result["id"])
        if result["tenant_id"] != tenant_id or result["kind"] != kind:
            raise ValueError()
        if (
            type(result["version"]) is not int
            or result["version"] < 1
            or type(result["active"]) is not bool
        ):
            raise ValueError()
        if operation in PATCH_OPERATIONS:
            if (
                result["id"] != identifier
                or result["version"] != body["version"] + 1
                or result["active"] is not body["active"]
            ):
                raise ValueError()
        elif identifier is not None or result['version'] != 1 or result['active'] is not True:
            raise ValueError()
        if any(result.get(name) != body[name] for name in FIELDS[kind]):
            raise ValueError()
        if kind == "capacities" and type(result["quantity"]) is not int:
            raise ValueError()
        if kind == "sites" and result.get("parent_id") is not None:
            raise ValueError()
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ContractError(
            "La respuesta no corresponde al registro institucional solicitado."
        ) from exc
    return result


def catalogue_dialog(window, kind, item=None, *, worker_factory=None):
    """Devuelve cuerpo o None. Todas las consultas se ejecutan mediante Work."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )

    if kind not in FIELDS:
        raise ValueError("Catálogo no disponible.")
    client = window.client

    def identity():
        user = client.user or {}
        return user.get("id"), user.get("tenant_id"), user.get("role")

    original_identity = identity()
    if original_identity[2] != "ADMIN":
        raise PermissionError(
            "La administración de sedes y capacidades corresponde a un administrador."
        )
    canonical_id(original_identity[0])
    canonical_id(original_identity[1])
    if worker_factory is None:
        from .app import Work

        worker_factory = Work
    if item is not None:
        validate_catalogue_item(kind, item, original_identity[1])
        item = dict(item)
    noun = "sede" if kind == "sites" else "capacidad"
    dialog = QDialog(window)
    dialog.setWindowTitle(("Corregir " if item is not None else "Registrar ") + noun)
    dialog.resize(680, 620 if kind == "capacities" and item is None else 420)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    heading = QLabel(dialog.windowTitle())
    heading.setObjectName("title")
    layout.addWidget(heading)
    if item is not None:
        layout.addWidget(
            QLabel(
                "La corrección conserva el registro anterior en el historial."
            )
        )
    state = {
        "alive": True,
        "busy": False,
        "parent_id": item.get("parent_id") if item else None,
        "parent_ready": kind == "sites",
        "rows": [],
        "page": 1,
        "total": 0,
        "body": None,
    }
    widgets = {}
    status = QLabel()
    status.setWordWrap(True)
    status.setAccessibleName("Estado del formulario institucional")
    form = QFormLayout()

    def text_field(key, label):
        widget = QLineEdit(str(item.get(key, "")) if item else "")
        widget.setMaxLength(200)
        widget.setObjectName("catalogue_" + key)
        widget.setAccessibleName(label)
        widgets[key] = widget
        form.addRow(label, widget)

    text_field("name", "Nombre")
    if kind == "sites":
        text_field("municipality", "Municipio")
        text_field("address", "Domicilio")
    else:
        text_field("component", "Componente registrado")
        quantity = QSpinBox()
        quantity.setRange(0, 100000)
        quantity.setObjectName("catalogue_quantity")
        quantity.setValue(item.get("quantity", 0) if item else 0)
        widgets["quantity"] = quantity
        form.addRow("Cantidad", quantity)
    layout.addLayout(form)

    table = search = previous = following = retry = page_label = None
    if kind == "capacities":
        if item is None:
            tools = QHBoxLayout()
            search = QLineEdit()
            search.setMaxLength(200)
            search.setPlaceholderText("Buscar sede por nombre")
            search.setAccessibleName("Buscar sede por nombre")
            retry = QPushButton("Buscar sede")
            tools.addWidget(search)
            tools.addWidget(retry)
            layout.addLayout(tools)
            table = QTableWidget(0, 2)
            table.setHorizontalHeaderLabels(("Sede", "Municipio"))
            table.setAccessibleName("Sedes disponibles para la capacidad")
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.verticalHeader().hide()
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            layout.addWidget(table, 1)
            paging = QHBoxLayout()
            previous, following = QPushButton("Anterior"), QPushButton("Siguiente")
            page_label = QLabel()
            paging.addWidget(previous)
            paging.addWidget(page_label)
            paging.addWidget(following)
            layout.addLayout(paging)
        else:
            parent_label = QLabel("Consultando la sede de esta capacidad…")
            parent_label.setWordWrap(True)
            layout.addWidget(parent_label)
            retry = QPushButton("Volver a consultar sede")
            layout.addWidget(retry)
    if item is not None:
        active = QCheckBox("Registro activo")
        active.setChecked(item["active"])
        widgets["active"] = active
        layout.addWidget(active)
        reason = QLineEdit()
        reason.setMaxLength(1000)
        reason.setAccessibleName("Motivo de la corrección")
        reason.setPlaceholderText("Motivo de la corrección")
        widgets["reason"] = reason
        layout.addWidget(QLabel("Motivo de la corrección"))
        layout.addWidget(reason)
        confirmation = QCheckBox(
            "Confirmo que revisé los datos y el estado antes de corregir"
        )
        widgets["human_confirmation"] = confirmation
        layout.addWidget(confirmation)
    layout.addWidget(status)
    actions = QHBoxLayout()
    cancel = QPushButton("Cancelar")
    cancel.setAutoDefault(False)
    save = QPushButton(
        "Guardar corrección" if item is not None else "Registrar " + noun
    )
    save.setObjectName("primary")
    save.setAutoDefault(False)
    actions.addStretch()
    actions.addWidget(cancel)
    actions.addWidget(save)
    layout.addLayout(actions)

    def current():
        return window.client is client and identity() == original_identity

    def values():
        result = {
            key: widget.isChecked()
            if key in ("active", "human_confirmation")
            else widget.value()
            if key == "quantity"
            else widget.text()
            for key, widget in widgets.items()
        }
        if kind == "capacities":
            result["parent_id"] = state["parent_id"]
        return result

    def ready(*_):
        try:
            catalogue_body(kind, values(), item)
            valid = True
        except ValueError:
            valid = False
        save.setEnabled(
            valid and current() and not state["busy"] and state["parent_ready"]
        )

    def launch(work, done):
        if state["busy"]:
            return
        state["busy"] = True
        ready()
        retry.setEnabled(False)
        if table is not None:
            table.setEnabled(False)
            previous.setEnabled(False)
            following.setEnabled(False)
        status.setText("Consultando sedes…")
        worker = worker_factory(work)
        window._request_workers = getattr(window, "_request_workers", [])
        window._request_workers.append(worker)

        def finish(callback, result):
            window._request_workers.remove(worker)
            if not state["alive"]:
                return
            state["busy"] = False
            if not current():
                status.setText(
                    "La sesión cambió. Cierra el formulario y vuelve a ingresar."
                )
                ready()
                return
            retry.setEnabled(True)
            if table is not None:
                table.setEnabled(True)
            callback(result)
            ready()

        def failed(_error):
            status.setText(
                "No se pudo consultar la sede. Revisa la conexión y vuelve a consultar; tus datos se conservan."
            )

        worker.signals.done.connect(lambda result: finish(done, result))
        worker.signals.failed.connect(lambda error: finish(failed, error))
        window.pool.start(worker)

    def fetch(page):
        if state["busy"]:
            return
        state.update(parent_id=None, parent_ready=False, rows=[])
        table.setRowCount(0)
        query = search.text().strip()

        def work():
            data = client.authorized(
                "identidad-acceso",
                "/api/v1/catalogues/sites",
                "sites_list_rows",
                params={"page": page, "page_size": 10, "q": query, "active": "true"},
            )
            if (
                type(data.get("page")) is not int
                or data["page"] != page
                or type(data.get("total")) is not int
                or data["total"] < 0
                or not isinstance(data.get("items"), list)
                or len(data["items"]) > 10
            ):
                raise ContractError("Página de sedes inválida.")
            for row in data["items"]:
                validate_catalogue_item("sites", row, original_identity[1])
                if row["active"] is not True:
                    raise ContractError("Sede no disponible para este formulario.")
            return data

        def done(data):
            state.update(rows=data["items"], page=data["page"], total=data["total"])
            table.setRowCount(len(state["rows"]))
            for row_index, row in enumerate(state["rows"]):
                for column, key in enumerate(("name", "municipality")):
                    table.setItem(row_index, column, QTableWidgetItem(row[key]))
            previous.setEnabled(page > 1)
            following.setEnabled(page * 10 < data["total"])
            page_label.setText(f"Página {page}")
            status.setText(
                "Selecciona la sede de esta capacidad."
                if data["items"]
                else "No hay sedes activas para esta búsqueda."
            )

        launch(work, done)

    def load_parent():
        state["parent_ready"] = False

        def work():
            parent_id = canonical_id(item.get("parent_id"))
            parent = client.authorized(
                "identidad-acceso",
                "/api/v1/catalogues/sites/" + parent_id,
                "sites_detail",
            )
            validate_catalogue_item("sites", parent, original_identity[1])
            if parent["id"] != parent_id:
                raise ContractError("La sede no corresponde a la capacidad.")
            return parent

        def done(parent):
            state["parent_ready"] = True
            parent_label.setText(
                "Sede: " + parent["name"] + ". La corrección no cambia su asociación."
            )
            status.setText("Revisa los campos y confirma la corrección.")

        launch(work, done)

    if kind == "capacities" and item is None:

        def select():
            index = table.currentRow()
            row = state["rows"][index] if 0 <= index < len(state["rows"]) else None
            state.update(parent_id=row["id"] if row else None, parent_ready=bool(row))
            if row:
                status.setText("Sede seleccionada: " + row["name"] + ".")
            ready()

        table.itemSelectionChanged.connect(select)
        retry.clicked.connect(lambda: fetch(1))
        search.returnPressed.connect(lambda: fetch(1))
        previous.clicked.connect(lambda: fetch(state["page"] - 1))
        following.clicked.connect(lambda: fetch(state["page"] + 1))
        fetch(1)
    elif kind == "capacities":
        retry.clicked.connect(load_parent)
        load_parent()
    else:
        status.setText(
            "Revisa los datos de la sede."
            if item is None
            else "Revisa los campos y confirma la corrección."
        )
    for key, widget in widgets.items():
        (
            widget.toggled
            if key in ("active", "human_confirmation")
            else widget.valueChanged
            if key == "quantity"
            else widget.textChanged
        ).connect(ready)

    def accept():
        if not current():
            status.setText(
                "La sesión cambió. Cierra el formulario y vuelve a ingresar."
            )
            ready()
            return
        try:
            state["body"] = catalogue_body(kind, values(), item)
        except ValueError as exc:
            status.setText(str(exc))
            return
        dialog.accept()

    cancel.clicked.connect(dialog.reject)
    save.clicked.connect(accept)
    dialog.finished.connect(lambda _: state.update(alive=False))
    widgets["name"].setFocus(Qt.OtherFocusReason)
    ready()
    return state["body"] if dialog.exec() == QDialog.Accepted else None
