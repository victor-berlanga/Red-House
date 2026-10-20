"""Negociación y fallos reales de conexión en la salud de cada propietario."""

from redhouse.config import MONGO_SERVICES


def test_health_contracts_dependency_failure_and_recovery_for_each_service(
    p, monkeypatch
):
    for service, app in p.apps.items():
        for dependency in (
            "live",
            "ready",
            "database",
            "redis",
            "mongodb",
            "storage",
            "worker",
        ):
            response = p.request(
                service,
                "GET",
                "/health/" + dependency,
                user=None,
                headers={"Accept": "text/plain"},
            )
            assert response.status_code == 406, (
                service,
                dependency,
                response.status_code,
            )
            assert response.json()["error"]["code"] == "not_acceptable"

        outages = [
            ("DATABASE_URL", "postgresql://invalid@127.0.0.1:1/missing", "database"),
            ("REDIS_URL", "redis://127.0.0.1:1/0", "redis"),
        ]
        if service in MONGO_SERVICES:
            outages.append(("MONGODB_URL", "mongodb://127.0.0.1:1", "mongodb"))
        for setting, unreachable, dependency in outages:
            path = "/health/" + dependency
            with monkeypatch.context() as outage:
                # The HTTP handler attempts a real connection to a closed port.
                # No response or dependency adapter is mocked.
                outage.setitem(app.config, setting, unreachable)
                response = p.request(service, "GET", path, user=None)
                assert response.status_code == 503, (service, dependency)
                assert response.json()["data"]["state"] == "down"
                response = p.request(service, "GET", "/health/ready", user=None)
                assert response.status_code == 503
                assert (
                    response.json()["data"]["dependencies"][dependency]["state"]
                    == "down"
                )
            response = p.request(service, "GET", path, user=None)
            assert response.status_code == 200
            assert response.json()["data"]["state"] == "up"
            assert (
                p.request(service, "GET", "/health/ready", user=None).status_code == 200
            )
