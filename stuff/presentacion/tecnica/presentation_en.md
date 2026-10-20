# Red House: implementation for the second assessment period

**Technical version · English · 12–15 minutes, including the demo.**

Application 0.3.0. Status as of October 20, 2026. Each section suggests one slide; the notes expand the spoken explanation.

## 1. The architecture we run

- A Python/Flask portal with Jinja2 and Highcharts charts based on real stored data.
- Ten microservices and one Monitoring service, separated by responsibility.
- The Docker portal uses `monolith` mode: it runs business modules within its own process.

**Speaker note:** The web application and microservices reuse the same versioned modules. The current portal does not need HTTP calls to the APIs for every operation. An HTTP mode is configurable, but failures do not trigger an automatic switch between modes. Updating a microservice image does not update the web image either.

## 2. Docker and API access

- Each service has its own Dockerfile and image, with two instances: A and B.
- Nginx provides a common entry point and distributes requests between both instances.
- The environment maintains 27 containers: 22 API instances, web, gateway, PostgreSQL, MongoDB, and Redis.

**Speaker note:** Each API instance also runs its worker; the portal has its own workers to process pending tasks. Volumes preserve data, and secrets remain outside the source code. The demonstrated redundancy covers API instances; the databases, gateway, and host remain single instances.

## 3. What each technology stores

| Technology | Specific purpose |
| --- | --- |
| PostgreSQL | One shared database with 71 domain tables and one technical table for portal logouts and pending revocations. |
| MongoDB | Events, auditing, custody, monitoring, and a rebuildable document view of shipment tracking. |
| Redis | Sessions, revocation, permissions, request limits, caching, and session renewal locks. |
| Google Cloud Storage | Private files; PostgreSQL stores their references and metadata. |

**Speaker note:** A shared SQL database does not mean shared administrative permissions: each module uses restricted credentials. The cache speeds up authorized queries; SQL constraints and locks protect the final reservation. MongoDB allows tracking information to be rebuilt without modifying the original history.

## 4. Authentication, sessions, and files

- Each protected request validates a JWT and checks session status, revocation, and permissions in Redis.
- The portal stores encrypted tokens in Redis; the browser receives a cookie containing an opaque identifier.
- PostgreSQL records logout and pending revocation; a worker completes pending work when Redis recovers.

**Speaker note:** Authorization considers the role, institution, and resource. Protected operations are rejected if Redis fails. If PostgreSQL fails, the portal cannot confirm global logout and returns 503. Files require authorization, content verification, and downloads through temporary signed URLs.

## 5. Business workflow and consistency

1. Register the resource and request; evaluate candidates and record human review.
2. Confirm a reservation without double booking the resource or exceeding the requested quantity.
3. Record transfer, delivery, and acceptance; update inventory, request, custody, notifications, and audit records.

**Speaker note:** Locks, constraints, and idempotency prevent duplicate operations. If a response is lost, the operation status is checked and the same operation key is retained. The outbox stores pending events in SQL; workers deliver them, and consumers recognize duplicates. The MongoDB projection uses versions to prevent an older event from replacing a later state.

**Algorithm boundary:** Evaluation and candidate ordering support human review. There is no automatic HLA interpretation or automatic clinical authorization.

## 6. Contracts and monitoring

- Versioned REST APIs provide JSON and XML responses, OpenAPI/Swagger documentation, and XML validation through XSD.
- Correlation identifiers connect requests, operations, and events to support error investigation.
- Health checks distinguish the process from its dependencies: PostgreSQL, Redis, MongoDB, and storage.

**Speaker note:** Monitoring shows availability, response times, errors, and history. Android will consume JSON and desktop will consume XML; both applications remain pending. Their contracts have already been tested, and future clients will access data through the APIs.

## 7. Evidence supporting the delivery

| Date | Verification | Result |
| --- | --- | --- |
| October 19 | Full regression for the delivery | 182 tests passed. |
| October 19 | Docker continuity | Nine checks passed, including web workflows with all 22 APIs stopped. |
| October 20 | Session update | A 121-test regression passed, followed by a successful final run of nine module tests. |
| October 20 | Restore after the update | 15,209 rows across 72 SQL tables preserved by count and hash; permissions verified. |

**Speaker note:** Runs have different scopes. Eight of the nine final tests already appear in the 121-test regression; they must not be added as unique tests. Evidence also covers JSON/XML, private GCS files, and dependency recovery. Tests using fictional data verify these scenarios without certifying production capacity or availability across hosts.

## 8. Demo and next stage

**Suggested demo, four minutes:**

1. Show a request, its review, and a prepared shipment; perform an authorized state transition.
2. Query the same resource through the API in JSON and XML using Swagger.
3. Show custody, audit records, and a verified file associated with the shipment.
4. Open the continuity evidence with APIs stopped and explain why the web application remains operational.

**Preparation:** Use fictional data and accounts for the required roles. Prepare queries and records, keeping credentials hidden. If uploading a file live, do so before closing the shipment. The [extended script, in Spanish](../Guion_segundo_parcial.md) contains the rehearsal procedure.

**Next stage:** Android, desktop, and production operations. Clinical validation, sustained load testing, and infrastructure redundancy also remain pending. The complete deployment now runs on a Google Compute Engine VM through its public IP over HTTPS, without local services, with data copied from local Docker and private GCS storage. The [GCP verification, in Spanish](../../../documentation/evidencias/gcp/RESULTADOS.md) covers the blood workflow, JSON/XML, sessions, and files.

---

Supporting sources, in Spanish: [October 19 results](../../../documentation/evidencias/segundo-parcial/RESULTADOS.md) · [October 20 sessions](../../../documentation/evidencias/sesiones-redis/RESULTADOS.md) · [technical report](../../../documentation/markdowns/Reporte_tecnico_segundo_parcial.md).

Other guides: [general version](../no_tecnica/presentation_en.md) · [versión en español](presentacion_es.md) · [index](../README.md).
