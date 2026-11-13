from redhouse.app import base_app, complete_app


VERSION = "0.4.4"


def create_app(config=None):
    from .routes import register

    app = base_app("priorizacion_geografia", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .academic import install as academic

    academic(app)
    from .decisions import install as decisions

    decisions(app)
    return complete_app(app)
