from redhouse.app import base_app, complete_app

VERSION = "0.4.4"


def create_app(config=None):
    from .routes import register

    app = base_app("compatibilidad", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .laboratory import install as laboratory

    laboratory(app)
    from .rules import install as rules

    rules(app)
    from .decision_data import install as decision_data

    decision_data(app)
    from .public_sources import install as public_sources

    public_sources(app)
    from redhouse.portal_metrics import install as portal_metrics

    portal_metrics(app, "compatibilidad")
    return complete_app(app)
