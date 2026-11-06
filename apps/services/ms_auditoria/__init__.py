from redhouse.app import base_app, complete_app


VERSION = "0.4.1"


def create_app(config=None):
    from .routes import register

    app = base_app("auditoria", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .anomalies import install as anomalies
    anomalies(app)
    return complete_app(app)
