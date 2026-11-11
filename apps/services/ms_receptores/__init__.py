from redhouse.app import base_app, complete_app


VERSION = "0.4.1"


def create_app(config=None):
    from .routes import register

    app = base_app("receptores", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .editing import install as editing

    editing(app)
    from .authorizations import install as authorizations

    authorizations(app)
    from .decision_data import install as decision_data
    decision_data(app)
    from redhouse.portal_metrics import install as portal_metrics
    portal_metrics(app, "receptores")
    return complete_app(app)
