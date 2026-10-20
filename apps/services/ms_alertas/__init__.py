from redhouse.app import base_app, complete_app


VERSION = "0.3.0"


def create_app(config=None):
    from .routes import register

    app = base_app("alertas", config)
    app.config["VERSION"] = VERSION
    register(app)
    return complete_app(app)
