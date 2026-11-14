"""Errores de guardas con categorías fijas, sin rutas ni credenciales."""

import errno

BUDGET_CODES = frozenset({"free_insufficient", "owned_limit_exceeded"})
CENSUS_CODES = frozenset(
    {"root_missing", "root_invalid", "root_changed", "symlink", "unstable"}
)
SAFE_ERRNOS = frozenset(
    {errno.ENOENT, errno.EACCES, errno.EPERM, errno.EIO, errno.ENOSPC, errno.ESTALE}
)


class BudgetExceeded(RuntimeError):
    def __init__(self, code, sample):
        if code not in BUDGET_CODES:
            raise ValueError("Invalid guard code")
        keys = {
            "free_bytes",
            "owned_bytes",
            "minimum_free_bytes",
            "maximum_owned_bytes",
        }
        if set(sample) != keys or any(
            type(value) is not int or value < 0 for value in sample.values()
        ):
            raise ValueError("Invalid guard sample")
        super().__init__(code)
        self.code = code
        self.sample = dict(sample)


class CensusFailure(ValueError):
    def __init__(self, code):
        if code not in CENSUS_CODES:
            raise ValueError("Invalid census code")
        super().__init__(code)
        self.code = code


def guard_diagnostic(error):
    """No copiar mensajes, rutas, DSN ni atributos arbitrarios del error."""
    if isinstance(error, BudgetExceeded):
        return {
            "class": "BudgetExceeded",
            "category": "budget",
            "code": error.code,
            **error.sample,
        }
    if isinstance(error, CensusFailure):
        return {"class": "CensusFailure", "category": "census", "code": error.code}
    if isinstance(error, OSError):
        return {
            "class": type(error).__name__
            if type(error) in (OSError, PermissionError, FileNotFoundError)
            else "OSError",
            "category": "filesystem_os",
            "errno": error.errno if error.errno in SAFE_ERRNOS else None,
        }
    return {
        "class": "ValueError" if type(error) is ValueError else "RuntimeError",
        "category": "guard_unknown",
    }
