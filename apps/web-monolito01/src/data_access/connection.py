from contextlib import contextmanager

import psycopg
from flask import current_app
from psycopg.rows import dict_row


@contextmanager
def transaction():
    """Una operación y su auditoría se confirman o revierten juntas."""
    with psycopg.connect(current_app.config["DATABASE_URL"], connect_timeout=3,
                         row_factory=dict_row,
                         options="-c search_path=red_house,pg_catalog -c statement_timeout=5000 -c timezone=UTC") as conn:
        yield conn
