from redhouse.app import base_app, complete_app


VERSION = "0.4.1"


def create_app(config=None):
    from .routes import register

    app = base_app("identidad_acceso", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .catalogue import install as catalogue

    catalogue(app)
    from .devices import install as devices

    devices(app)
    from .strong_auth import install as strong_auth

    strong_auth(app)
    from .accreditations import install as accreditations

    accreditations(app)
    from .portal import install as portal

    portal(app)
    return complete_app(app)
