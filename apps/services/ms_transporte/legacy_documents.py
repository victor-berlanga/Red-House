"""Adaptador v1: delega una sola vez al propietario; nunca escribe archivos."""

import json
from pathlib import Path

from flask import request
from redhouse import document_contracts
from redhouse.api import endpoint
from redhouse.client import call
from redhouse.models import Confirm


def install(app):
    for specification in json.loads(
        (
            Path(document_contracts.__file__).with_name("document_routes.json")
        ).read_text()
    ):
        spec = dict(specification)
        name = spec.pop("name")
        model_name = spec.pop("model")
        model = (
            (
                Confirm
                if model_name == "Confirm"
                else getattr(document_contracts, model_name)
            )
            if model_name
            else None
        )

        def make_handler(method, has_body):
            def forward(**params):
                path = request.path + (
                    ("?" + request.query_string.decode("ascii"))
                    if request.query_string
                    else ""
                )
                return call(
                    "documentos",
                    method,
                    path,
                    params.get("data") if has_body else None,
                    forward_headers=True,
                )

            return forward

        handler = make_handler(spec["method"], model is not None)
        handler.__name__ = name
        endpoint(app, model=model, **spec)(handler)
