# Red House: progress during the second assessment period

**General version · English · 8–10 minutes, including the demo.**

Status as of October 20, 2026. Use the points as slide content and the notes as speaking prompts.

## 1. The problem we address

- One institution has an available resource and another needs it.
- Red House organizes requests, availability, approvals, and transfers of blood and organs.
- Each stage records what happened and who took part.

**Speaker note:** We want institutions to share information and coordinate delivery. The system supports staff; medical decisions still require human authorization.

## 2. What we accomplished this period

- We integrated registration, requests, reservations, and transfers with real data storage.
- We prepared the portal and services in Docker, both locally and in Google Cloud.
- We added private files, shipment tracking, and recovery checks.

**Speaker note:** The main advance is the ability to complete entire workflows. An action updates records that authorized users can then view.

## 3. How a complete case works

1. The blood bank registers a resource, and a physician authorizes its availability.
2. Another institution registers a request and reviews the proposed candidates.
3. Authorized staff confirm the reservation and arrange the transfer.
4. The assigned person records delivery; the destination accepts it, updating inventory and the request.

**Speaker note:** Human review takes place before committing the resource. The process creates custody records, internal notifications, and an action history. Blood and organs follow distinct processes.

## 4. How the system is organized

- The portal provides screens based on each user's responsibilities.
- Ten microservices divide the tasks; an additional service monitors their status.
- Each service has its own container, with two instances in the Docker configuration.

**Speaker note:** A container packages what a component needs to run. The current portal also includes its own business modules: it can operate with the APIs stopped while its databases and other required dependencies remain available.

## 5. How we manage data and access

- Access depends on the user's role, institution, and relationship to the record.
- Redis stores sessions; PostgreSQL records logouts and pending revocations.
- Files remain private in Google Cloud Storage and are accessed through authorized temporary links.

**Speaker note:** PostgreSQL stores business operations, while MongoDB stores events and tracking information. This separation organizes information according to its purpose. The chain of custody shows who received or handed over a resource.

## 6. What we verified

- We checked 20 pages across seven roles and compared charts with stored data.
- We tested workflows with one instance of every API stopped, and the portal with all APIs stopped.
- We restored backups and verified private file uploads and downloads.

**Speaker note:** These results come from tests using fictional data. General checks were performed on October 19; the session update was verified on October 20. The checks demonstrate specific cases of operation and recovery.

## 7. Short demo: about three minutes

1. **Show the need:** open a request and the available inventory.
2. **Explain the decision:** show candidates, human review, and a prepared reservation.
3. **Perform a real action:** upload a fictional evidence file to an open shipment, verify it, and download it with authorization.
4. **Show the result:** open a completed shipment, its custody history, and the fulfilled request.

**Preparation:** Have the records and authorized accounts ready before starting. Explain which stages were prepared beforehand. Evidence is uploaded during an open shipment; new uploads are rejected after closure.

## 8. What comes next

- Develop the Android and desktop applications using the prepared APIs.
- Expand capacity and recovery testing on the VM. The system already opens through its IP over HTTPS, with no local services required.
- Extend load testing, infrastructure redundancy, and clinical validation of the rules.

**Speaker note:** We currently have a tested Docker environment, a VM accessible through a private connection, and real cloud files. The next stage includes public access and the validation required for real operations.

---

Supporting material: [usage guide and evidence](../README.md) · [technical version](../tecnica/presentation_en.md) · [versión en español](presentacion_es.md).
