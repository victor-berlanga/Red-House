# What to say and demonstrate for the second assessment

English guide for the in-person presentation and the YouTube video. Based on the project state on **October 20, 2026** and the shared assignment. Timings are rehearsal suggestions; follow the instructor's time limit. [Versión en español](guion_es.md).

Follow one concrete operation and show its results. Each technology needs visible evidence as well as an explanation. The commands below support the person operating the demo; they do not need to be read aloud.

## 1. Preparation

- Open the [GCP portal](https://34.18.186.116), [Identity Swagger](https://34.18.186.116/services/identidad-acceso/docs/), [Inventory Swagger](https://34.18.186.116/services/inventario/docs/), and an SSH terminal for the `red-house` VM. All processing runs on GCP; do not start local Docker or application servers.
- Sign in to the portal as `operator1` before creating the Swagger session. Use the credentials already provided to the team without copying them into these documents. Cover passwords, tokens, and cookies while recording, including Swagger's generated Curl section.
- Prepare a new fictional reference, such as `DEMO-YYYYMMDD-01`, and a future expiration date with a time zone. Reserve that reference for the demo.
- For the shipment process, prepare your own fictional case with a request, reservation, and valid shipment assigned to `transport1`. Leave it **In transit**, with no pending inventory changes. Have `operator2` available if Hospital 2 is the destination, and `auditor1` for the audit trail. Use separate browser profiles when keeping multiple accounts signed in.
- Distribute the blocks among all team members. Each person should explain a responsibility and execute or interpret evidence. Assign names during rehearsal.

## 2. In-person presentation: 16–18 minutes

| Block | What to say | What to show | Time |
| --- | --- | --- | --- |
| Problem and scope | “Red House helps institutions coordinate resources, requests, and shipments.” | Portal and a need involving two hospitals. | 1 min |
| Current architecture | “We have an autonomous portal and independent APIs that share rules and authorized storage.” | Portal, Swagger, and the system's GCP deployment. | 1 min |
| Web system and process | “Each role can perform specific actions, and changes retain a history.” | Prepared shipment; record authorized delivery and acceptance. | 3 min |
| Microservices, Swagger, and formats | “This request reaches an independent service and returns real data.” | API creation, JSON/XML reads of that record, and its appearance in the portal. | 4 min |
| JWT and Redis | “The token identifies the session; Redis lets us check whether it is still active.” | Authorized query, session TTL, logout, and rejection of the same token. | 3 min |
| PostgreSQL, MongoDB, and Docker | “We can follow this operation from its response to storage and the container that handled it.” | SQL row, MongoDB document, containers, and request log. | 4 min |
| Limits and next stage | “This delivery demonstrates academic operation with fictional data; mobile and desktop remain pending.” | Monitoring and a reference to recorded tests. | 1 min |

**Clarification to include when explaining the architecture:**

> “The current portal runs in monolithic mode: it executes its modules inside the web process. The APIs are also deployed in independent containers, and we will use them directly through Swagger. They share rules and authorized data. Seeing a record in both interfaces demonstrates consistency; the API request and its Docker log demonstrate use of the independent microservice.”

## 3. Demonstrate the process in the portal

Open the prepared shipment as `transport1`. Show its originating request and reservation, assigned operator, and previous steps. Explain that these prerequisites were prepared before the presentation.

1. From **En tránsito** (In transit), record **Entregado** (Delivered), with a fictional reason and confirmation.
2. As the destination institution's operator —`operator2` in the prepared case— record **Aceptado** (Accepted). Complete the destination location if requested by the form.
3. Inspect the custody chain, resource status, and linked request. If that request required one unit and is now fully satisfied, it should be closed.
4. As `auditor1`, open the [audit trail](https://34.18.186.116/auditoria), locate the acceptance event, and open its details. Check the shipment identifier, action, source, and traceability there. If pending, wait for synchronization and refresh.

**Suggested narration:** “We can see who acted, what changed, and the recorded outcome. Acceptance documents a logistical delivery. Allocation requires human review and does not represent a completed transfusion or transplant.”

## 4. Demonstrate APIs, JSON/XML, JWT, and Redis

### A. Independent sign-in

1. In Inventory Swagger, execute `GET /api/v1/resources` **without Authorize**. Expected result: `401`.
2. In Identity Swagger, use `POST /api/v1/auth/login` with `operator1` and its password. Select a JSON body. Expected result: `200`.
3. Copy `data.access_token` into **Authorize** in both Inventory and Identity. Paste only the token, without adding `Bearer` again. The portal session and this API session are separate.

**Suggested narration:** “The service requires authentication. The JWT has a limited lifetime, and permissions depend on the user and institution.”

### B. Create a real record through the microservice

In Inventory, execute `POST /api/v1/resources`. Select `Content-Type: application/json`, supply a new `Idempotency-Key`, such as `demo-create-YYYYMMDD-01`, and use this body **after replacing the reference and date**:

```json
{
  "folio": "DEMO-YYYYMMDD-01",
  "kind": "BLOOD",
  "component": "RBC",
  "blood_group": "O-",
  "expires_at": "FUTURE_ISO_8601_DATE_WITH_TIME_ZONE",
  "donation_id": null,
  "location_id": null,
  "collected_at": null
}
```

The date must use `YYYY-MM-DDTHH:MM:SSZ` format and be in the future on the rehearsal day. This is fictional input, not a clinical storage rule. Expect `201` and status `QUARANTINE`.

Keep **`data.id`** and **`meta.correlation_id`** from creation. These are the two references used in section 5. To retry the same operation after a lost response, retain the body and key; for a new record, use a new reference and key.

As `operator1`, search for the reference in the [portal Inventory](https://34.18.186.116/inventario) and open it. Show that it matches the record created through the API.

**Suggested narration:** “We just created this record through Inventory. The portal can read it because both use shared storage with their respective permissions.”

### C. Show JSON and XML for the same query

Execute `GET /api/v1/resources/{identifier}` with the previous `data.id`. Show **Request URL**, status `200`, `meta.service`, and the actual **Server response** body.

Repeat the query, selecting `application/json` and then `application/xml` as the response format. Use Swagger's response content type selector; if `Accept` is also shown, keep it consistent. Check the returned `Content-Type`: changing **Example Value** alone does not execute a new request.

Compare the same identifier and reference in both responses. Open the [Inventory response XSD](https://34.18.186.116/services/inventario/schemas/response.xsd) as a structure reference; viewing it does not validate an XML document.

**Suggested narration:** “These are the same data expressed in two formats. Contracts are ready for JSON and XML clients; mobile and desktop applications are not part of this delivery yet.”

### D. Show the session and its revocation

1. Run the Redis inspection in section 5. It should show `exists: 1` and `ttl_seconds` greater than zero.
2. In Identity, execute `POST /api/v1/auth/logout`, authorized with the same JWT and a new `Idempotency-Key`, such as `demo-logout-YYYYMMDD-01`. No body is required. Expect `200` and `revoked: true`.
3. Repeat the Inventory query with **the same previous token**. Expected result: `401`.
4. Repeat the Redis inspection. For that session, `exists: 0` and TTL `-2` indicate that the key no longer exists.

Do not create another `operator1` session between the two inspections: the command selects that user's latest sign-in. If the JWT expires before finishing this block, sign in again and repeat the complete block.

**Suggested narration:** “Redis maintains temporary session state. After logout, keeping a copy of the token no longer grants access.”

## 5. VM evidence: supporting queries

Open **Google Cloud → Compute Engine → red-house → SSH**. Alternatively, from a terminal with access to the account:

```sh
gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a
```

**Run all commands below inside that SSH session**, using existing containers. These are administrative inspection queries for the presentation. Client applications do not access the databases directly. The examples read private configuration inside the container and print only selected fields.

### PostgreSQL: the row created through Swagger

Replace `PASTE_RESOURCE_UUID` with the creation response's `data.id`:

```sh
sudo docker compose -f /opt/redhouse/compose.yaml exec -T inventario-a python - <<'PY'
import json
from pathlib import Path
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
c = json.loads(Path('/run/secrets/config').read_text())
identifier = str(UUID('PASTE_RESOURCE_UUID'))
with psycopg.connect(c['DATABASE_URL'], connect_timeout=3, row_factory=dict_row) as db:
    db.execute('SET TRANSACTION READ ONLY')
    row = db.execute(
        'SELECT id,folio,status,version FROM access_inventario.resources WHERE id=%s',
        (identifier,),
    ).fetchone()
print(json.dumps(row, default=str))
PY
```

**Show:** the same identifier, reference, and status. `access_inventario.resources` is an access view over the shared PostgreSQL database, not another copy of the data.

### MongoDB: the audit document for that creation

Replace `PASTE_CORRELATION_UUID` with `meta.correlation_id` from the **creation POST**, not a later query:

```sh
sudo docker compose -f /opt/redhouse/compose.yaml exec -T auditoria-a python - <<'PY'
import json
from pathlib import Path
from uuid import UUID
from pymongo import MongoClient
c = json.loads(Path('/run/secrets/config').read_text())
correlation = str(UUID('PASTE_CORRELATION_UUID'))
with MongoClient(c['MONGODB_URL'], serverSelectionTimeoutMS=3000) as client:
    row = client[c['MONGODB_DATABASE']].events.find_one(
        {'correlation_id': correlation, 'action': 'RESOURCE_CREATED'},
        {'_id': 0, 'source': 1, 'action': 1, 'resource_id': 1,
         'correlation_id': 1, 'occurred_at': 1},
    )
print(json.dumps(row, default=str))
PY
```

**Show:** `source: inventario`, `action: RESOURCE_CREATED`, and a `resource_id` matching the SQL row. If the result is `null`, wait a few seconds and retry: workers deliver events in the background. If it persists, inspect the actual state; label any earlier screenshot as historical evidence.

**Suggested narration:** “PostgreSQL holds the operational record, and MongoDB stores this event document. MongoDB also holds custody, monitoring, and shipment tracking events.” The regular Audit page reads SQL; this command queries MongoDB directly.

### Redis: existence and expiration of the API session

Run after the Swagger login and repeat after its logout. The command prints no tokens or passwords:

```sh
sudo docker compose -f /opt/redhouse/compose.yaml exec -T identidad-acceso-a python - <<'PY'
import json
from pathlib import Path
import psycopg
import redis
c = json.loads(Path('/run/secrets/config').read_text())
with psycopg.connect(c['DATABASE_URL'], connect_timeout=3) as db:
    db.execute('SET TRANSACTION READ ONLY')
    row = db.execute(
        'SELECT s.id FROM access_identidad_acceso.sessions s '
        'JOIN access_identidad_acceso.users u ON u.id=s.user_id '
        'WHERE u.username=%s ORDER BY s.expires_at DESC LIMIT 1',
        ('operator1',),
    ).fetchone()
if row is None:
    raise SystemExit('No session found: sign in through Swagger first.')
sid = str(row[0])
with redis.Redis.from_url(c['REDIS_URL'], socket_timeout=3, socket_connect_timeout=3) as cache:
    key = c['REDIS_PREFIX'] + 'session:' + sid
    print(json.dumps({'session_ref': sid[:8], 'exists': cache.exists(key),
                      'ttl_seconds': cache.ttl(key)}))
PY
```

**Suggested narration:** “TTL is the remaining lifetime of this session key. It is not necessarily the JWT's remaining lifetime. Redis also maintains permissions, revocations, request limits, and cache.”

### Docker: containers and the handled request

```sh
sudo docker compose -f /opt/redhouse/compose.yaml ps
sudo docker compose -f /opt/redhouse/compose.yaml logs --since 20m --no-color inventario-a inventario-b | grep -F -- 'PASTE_CORRELATION_UUID'
```

Replace the UUID with the creation correlation identifier. In the logs, show the service, `POST` method, `/api/v1/resources` route, `201` status, and response time. The container prefix identifies which replica handled the request.

The configuration has 27 runtime containers: 22 API instances, web, gateway, and three data stores. Show the actual state reported by `ps`; the preparation container `bootstrap` may appear stopped when using `ps -a`.

**Suggested narration:** “Each service has its own container and can be deployed separately. This line belongs to the request we just executed.” Then open [Monitoring](https://34.18.186.116/monitoreo) as `admin1`, `coordinator1`, or `auditor1`; its indicators show availability, while the log demonstrates this specific request.

## 6. YouTube adaptation: 18–22 minutes

Use the same sequence, with more room to explain requests and results:

| Chapter | Content and suggested capture |
| --- | --- |
| 00:00–02:00 | Problem, institutions, and objective. Portal on screen; no required cover slide. |
| 02:00–04:00 | Current architecture: autonomous portal, APIs, Docker, GCP, and each storage system's purpose. |
| 04:00–08:00 | Web process: prepared prerequisites, delivery, acceptance, request, and custody. |
| 08:00–13:00 | Executed Swagger requests: login, creation, JSON/XML, and matching portal record. |
| 13:00–18:00 | JWT/Redis before and after logout; PostgreSQL row, MongoDB document, and Docker logs. |
| 18:00–20:00 | Monitoring, test evidence, and actual pending work. Up to two extra minutes for common questions. |

Narrate each operation with four ideas: **what we are doing, what we send, what came back, and where it was recorded**. Capture actual `Server response` results; contract examples and historical screenshots are labeled supporting material. If including GCS, show a small fictional shipment attachment and its authorized download without exposing the full signed URL.

Each team member needs an identifiable contribution and an explanation of their responsibility. The team assigns names. Publish the video as **public or unlisted**, never private, and check that its link opens in a signed-out window. This document does not establish that recording or publication has already happened.

## 7. Short answers for instructor questions

- **Where are microservices actually used?** In the `/services/...` requests executed through Swagger; we show the response and container log. The current portal uses internal modules.
- **Why Redis?** For sessions and temporary controls that need fast access and expiration, as well as caching.
- **Why MongoDB when PostgreSQL exists?** To retain event documents and tracking views; PostgreSQL maintains transactional operations.
- **Why Docker?** To run and update each component separately with reproducible dependencies.
- **What demonstrates integration?** The same operation has matching identifiers across the API, portal, storage, and audit trail, while permissions still apply.
- **What remains pending?** Android, desktop, clinical validation, and production operating conditions. Do not claim availability across machines: the current deployment uses one VM.

## Rehearsal references

The following reference documents are in Spanish; source files use the project's implementation language.

- [Current status](../../PROJECT_STATUS.md) and [GCP operation](../../deployment/gcp/README.md).
- [Verified GCP results](../../documentation/evidencias/gcp/RESULTADOS.md).
- [Brief technical presentation in English](../presentacion/tecnica/presentation_en.md).
- [Contracts and headers](../../apps/services/redhouse/openapi.py), [inventory creation](../../apps/services/ms_inventario/routes.py), and [PostgreSQL model](../../data/database/schema.sql).

Commands were checked against source code and deployment configuration. This guide does not represent a new test run against the VM; rehearse with fresh references and dates before presenting.
