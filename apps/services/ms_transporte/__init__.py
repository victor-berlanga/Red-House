from redhouse.app import base_app, complete_app


VERSION = "0.3.0"


def create_app(config=None):
    from .routes import register

    app = base_app("transporte", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .projection import install as projection
    from .routes import shipment_access

    projection(app, shipment_access)
    return complete_app(app)
