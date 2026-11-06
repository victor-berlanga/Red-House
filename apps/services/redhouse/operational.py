"""Explicit deployment scope; clinical authority always comes from its owner."""

from flask import current_app

from .errors import APIError


def require_clinical_policy(result):
    scope = current_app.config["OPERATION_SCOPE"]
    if scope == "ACADEMIC":
        return
    if scope != "CLINICAL" or not result or not result.get("clinical_enabled"):
        raise APIError(
            "clinical_policy_disabled",
            "Perfil académico o sin aprobación competente vigente; operación clínica deshabilitada.",
            409,
        )


def require_execution_scope(snapshot, review=None):
    """A deployment change never promotes an academic execution or review."""
    if current_app.config["OPERATION_SCOPE"] == "CLINICAL" and (
        snapshot.get("operation_scope") != "CLINICAL"
        or (review is not None and review.get("operation_scope") != "CLINICAL")
    ):
        raise APIError(
            "academic_execution",
            "Una ejecución o dictamen académico requiere nueva evaluación clínica.",
            409,
        )
