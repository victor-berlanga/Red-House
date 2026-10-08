CREATE TABLE alerts(id uuid PRIMARY KEY,event_id uuid NOT NULL,tenant_id uuid NOT NULL,region_id uuid NOT NULL,
 target_role text NOT NULL,target_user_id uuid,message_code text NOT NULL,resource_id text NOT NULL,status text NOT NULL DEFAULT 'OPEN',
 acknowledged_by uuid,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(event_id,tenant_id,target_role));
