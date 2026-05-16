CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  code TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE roles (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  role_id UUID NOT NULL REFERENCES roles(id),
  username TEXT NOT NULL,
  display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, username)
);

CREATE TABLE sites (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE (tenant_id, code)
);

CREATE TABLE lines (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  site_id UUID NOT NULL REFERENCES sites(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE (tenant_id, code)
);

CREATE TABLE equipment_families (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE (tenant_id, code)
);

CREATE TABLE equipment (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  line_id UUID NOT NULL REFERENCES lines(id),
  family_id UUID NOT NULL REFERENCES equipment_families(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  vendor TEXT,
  model TEXT,
  revision TEXT,
  status TEXT NOT NULL DEFAULT 'NORMAL',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, code)
);

CREATE TABLE alarm_codes (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  equipment_family_id UUID NOT NULL REFERENCES equipment_families(id),
  code TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  primary_signal TEXT,
  recommended_first_check TEXT,
  UNIQUE (tenant_id, equipment_family_id, code)
);

CREATE TABLE io_points (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  equipment_id UUID NOT NULL REFERENCES equipment(id),
  code TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('DI','DO')),
  signal_type TEXT NOT NULL,
  description TEXT NOT NULL,
  normal_state BOOLEAN,
  related_alarm_code TEXT,
  UNIQUE (tenant_id, equipment_id, code)
);

CREATE TABLE ethercat_devices (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  equipment_id UUID NOT NULL REFERENCES equipment(id),
  slave_no INT NOT NULL,
  name TEXT NOT NULL,
  expected_state TEXT NOT NULL CHECK (expected_state IN ('INIT','PRE_OP','SAFE_OP','OP')),
  vendor_id TEXT,
  product_code TEXT,
  UNIQUE (tenant_id, equipment_id, slave_no)
);

CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  evidence_code TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  related_alarm_code TEXT,
  embedding vector(1536),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, evidence_code)
);

CREATE TABLE diagnosis_sessions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  equipment_id UUID NOT NULL REFERENCES equipment(id),
  created_by_user_id UUID NOT NULL REFERENCES users(id),
  alarm_code TEXT NOT NULL,
  symptom_summary TEXT NOT NULL,
  log_excerpt TEXT,
  ethercat_state TEXT,
  io_snapshot JSONB NOT NULL,
  recent_action TEXT,
  status TEXT NOT NULL CHECK (status IN ('CREATED','ANALYZING','ANALYSIS_READY','INSUFFICIENT_EVIDENCE','CLOSED')) DEFAULT 'CREATED',
  risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')) DEFAULT 'LOW',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_runs (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  session_id UUID NOT NULL REFERENCES diagnosis_sessions(id),
  status TEXT NOT NULL CHECK (status IN ('COMPLETED','INSUFFICIENT_EVIDENCE','SAFETY_BLOCKED','FAILED')),
  mode TEXT NOT NULL DEFAULT 'DETERMINISTIC',
  safety_result TEXT NOT NULL DEFAULT 'SAFE_READ_ONLY',
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE agent_steps (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  agent_run_id UUID NOT NULL REFERENCES agent_runs(id),
  step_order INT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  summary TEXT,
  details JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (agent_run_id, step_order)
);

CREATE TABLE diagnosis_hypotheses (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  agent_run_id UUID NOT NULL REFERENCES agent_runs(id),
  rank INT NOT NULL,
  title TEXT NOT NULL,
  reasoning TEXT NOT NULL,
  confidence_band TEXT NOT NULL CHECK (confidence_band IN ('HIGH','MEDIUM','LOW')),
  risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
  recommended_next_checks JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (agent_run_id, rank)
);

CREATE TABLE evidence_links (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  hypothesis_id UUID REFERENCES diagnosis_hypotheses(id),
  source_type TEXT NOT NULL,
  source_code TEXT NOT NULL,
  title TEXT NOT NULL,
  excerpt TEXT NOT NULL,
  relevance_reason TEXT NOT NULL
);

CREATE TABLE inspection_plan_items (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  agent_run_id UUID NOT NULL REFERENCES agent_runs(id),
  item_order INT NOT NULL,
  title TEXT NOT NULL,
  instruction TEXT NOT NULL,
  expected_observation TEXT,
  safety_level TEXT NOT NULL CHECK (safety_level IN ('NORMAL','CAUTION','APPROVAL_REQUIRED')) DEFAULT 'NORMAL',
  evidence_codes JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (agent_run_id, item_order)
);

CREATE TABLE checklist_runs (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  diagnosis_session_id UUID NOT NULL REFERENCES diagnosis_sessions(id),
  agent_run_id UUID NOT NULL REFERENCES agent_runs(id),
  created_by_user_id UUID NOT NULL REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('CREATED','IN_PROGRESS','COMPLETED','BLOCKED')) DEFAULT 'CREATED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE checklist_items (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  checklist_run_id UUID NOT NULL REFERENCES checklist_runs(id),
  source_inspection_plan_item_id UUID NOT NULL REFERENCES inspection_plan_items(id),
  item_order INT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  expected_result TEXT,
  status TEXT NOT NULL CHECK (status IN ('TODO','IN_PROGRESS','DONE','BLOCKED','SKIPPED')) DEFAULT 'TODO',
  field_note TEXT,
  completed_by_user_id UUID REFERENCES users(id),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (checklist_run_id, item_order)
);

CREATE TABLE reports (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  session_id UUID NOT NULL REFERENCES diagnosis_sessions(id),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED')) DEFAULT 'DRAFT',
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE approval_requests (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  target_type TEXT NOT NULL,
  target_id UUID NOT NULL,
  requested_by UUID NOT NULL REFERENCES users(id),
  approver_id UUID REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED')) DEFAULT 'PENDING',
  requested_reason TEXT,
  decision_comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at TIMESTAMPTZ
);

CREATE TABLE policy_violations (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  session_id UUID REFERENCES diagnosis_sessions(id),
  detected_keyword TEXT NOT NULL,
  violation_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  action_taken TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  actor_user_id UUID REFERENCES users(id),
  event_type TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id UUID,
  severity TEXT NOT NULL CHECK (severity IN ('INFO','WARNING','ERROR','SECURITY')),
  payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_equipment_tenant_id ON equipment(tenant_id);
CREATE INDEX idx_alarm_codes_tenant_family ON alarm_codes(tenant_id, equipment_family_id);
CREATE INDEX idx_io_points_equipment ON io_points(tenant_id, equipment_id);
CREATE INDEX idx_diagnosis_sessions_tenant_equipment ON diagnosis_sessions(tenant_id, equipment_id);
CREATE INDEX idx_agent_runs_session ON agent_runs(tenant_id, session_id);
CREATE INDEX idx_agent_steps_run ON agent_steps(agent_run_id);
CREATE INDEX idx_evidence_links_hypothesis ON evidence_links(hypothesis_id);
CREATE INDEX idx_checklist_runs_tenant_session ON checklist_runs(tenant_id, diagnosis_session_id);
CREATE INDEX idx_checklist_runs_agent_run ON checklist_runs(tenant_id, agent_run_id);
CREATE INDEX idx_checklist_items_run ON checklist_items(checklist_run_id);
CREATE INDEX idx_audit_events_tenant_created ON audit_events(tenant_id, created_at DESC);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
