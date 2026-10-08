CREATE TABLE recipients(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,folio text NOT NULL,display_name text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('BLOOD','ORGAN')),blood_group text NOT NULL,organ_type text,
 studies text NOT NULL,status text NOT NULL DEFAULT 'ACTIVE',version integer NOT NULL DEFAULT 1,UNIQUE(tenant_id,folio),
 CHECK((kind='BLOOD' AND organ_type IS NULL) OR (kind='ORGAN' AND organ_type IN ('KIDNEY','LIVER','HEART'))));
CREATE TABLE requests(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,recipient_id uuid NOT NULL REFERENCES recipients(id),
 kind text NOT NULL,component text NOT NULL,quantity integer NOT NULL CHECK(quantity>0),urgency integer NOT NULL CHECK(urgency BETWEEN 1 AND 3),
 status text NOT NULL DEFAULT 'OPEN',version integer NOT NULL DEFAULT 1,created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(kind<>'ORGAN' OR quantity=1));
CREATE UNIQUE INDEX active_organ_request ON requests(recipient_id) WHERE kind='ORGAN' AND status IN ('OPEN','IN_PROGRESS');
CREATE TABLE holds(id uuid PRIMARY KEY,request_id uuid NOT NULL REFERENCES requests(id),recipient_id uuid NOT NULL REFERENCES recipients(id),
 operation_id uuid NOT NULL UNIQUE,resource_id uuid NOT NULL,kind text NOT NULL,request_version integer NOT NULL,region_id uuid NOT NULL,
 status text NOT NULL DEFAULT 'HELD',created_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX organ_patient_reserved ON holds(recipient_id) WHERE kind='ORGAN' AND status IN ('HELD','CONFIRMED','RECEIVED');
