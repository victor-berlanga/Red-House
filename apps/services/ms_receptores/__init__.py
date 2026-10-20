from redhouse.app import base_app, complete_app


VERSION = "0.3.0"


def create_app(config=None):
    from .routes import register

    app = base_app("receptores", config)
    app.config["VERSION"] = VERSION
    register(app)
    from .queries import install

    install(app)
    from .editing import install as editing

    editing(app)
    return complete_app(app)
