from redhouse.app import base_app, complete_app


VERSION = "0.3.0"


def create_app(config=None):
    from .routes import register

    app = base_app("identidad_acceso", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .catalogue import install as catalogue

    catalogue(app)
    return complete_app(app)
