CREATE TABLE institutions(id uuid PRIMARY KEY,name text NOT NULL,region_id uuid NOT NULL,active boolean NOT NULL DEFAULT true);
CREATE TABLE users(id uuid PRIMARY KEY,tenant_id uuid NOT NULL REFERENCES institutions(id),username text NOT NULL UNIQUE,
 password_hash text NOT NULL,role text NOT NULL CHECK(role IN ('ADMIN','OPERATOR','MEDICAL','COORDINATOR','TRANSPORT','AUDITOR','DONOR')),
 active boolean NOT NULL DEFAULT true,version integer NOT NULL DEFAULT 1);
CREATE TABLE sessions(id uuid PRIMARY KEY,user_id uuid NOT NULL REFERENCES users(id),expires_at timestamptz NOT NULL,revoked_at timestamptz);
