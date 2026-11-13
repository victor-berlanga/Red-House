from redhouse.app import base_app, complete_app


VERSION = "0.4.1"


def create_app(config=None):
    from .routes import register

    app = base_app("transporte", config)
    app.config["VERSION"] = VERSION
    from redhouse.proxy import TrustedProxy, trusted_peer

    peer = trusted_peer(app.config)
    if peer:
        app.wsgi_app = TrustedProxy(app.wsgi_app, peer)
    register(app)
    from .queries import install

    install(app)
    from .projection import install as projection
    from .routes import shipment_access

    projection(app, shipment_access)
    from .tracking import install as tracking

    tracking(app)
    from .mobile import install as mobile
    mobile(app)
    from .synchronization import install as synchronization

    synchronization(app)
    from .legacy_documents import install as documents

    documents(app)
    from .analytics import install as analytics

    analytics(app)
    from .decision_data import install as decision_data
    decision_data(app)
    from redhouse.portal_metrics import install as portal_metrics
    portal_metrics(app, "transporte")
    return complete_app(app)
