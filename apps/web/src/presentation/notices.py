from flask import flash, url_for
from markupsafe import Markup


def created(message, label, endpoint, **args):
    # Escape automático incluso si el folio/nombre procede de una captura.
    flash(
        Markup('{} <strong>{}</strong> · <a href="{}">Ver registro</a>').format(
            message, label, url_for(endpoint, **args)
        ),
        "success",
    )
