from redhouse.app import base_app, complete_app


VERSION = "0.4.1"


def create_app(config=None):
    from .routes import register

    app = base_app("inventario", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .editing import install as editing

    editing(app)
    from .quality import install as quality

    quality(app)
    from .interoperability import install as interoperability

    interoperability(app)
    from .analytics import install as analytics
    from .traceability import install as traceability

    analytics(app)
    traceability(app)
    from .decision_data import install as decision_data
    decision_data(app)
    return complete_app(app)
