"use client";

import { useEffect, type ReactNode } from "react";
import { Clock, Database, FileJson, Link2, ShieldCheck, UserRound, X } from "lucide-react";
import { CodePill, StatusBadge } from "./operational";
import {
  WorkflowTraceList,
  checklistRunTraceHref,
  diagnosisSessionTraceHref,
  reportDraftTraceHref,
  type WorkflowTraceReference,
} from "./workflow-trace";

export type AuditEventSummary = {
  id?: string | null;
  audit_event_id?: string | null;
  event_type?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  severity?: string | null;
  actor?: string | null;
  actor_name?: string | null;
  actor_role?: string | null;
  actor_user_id?: string | null;
  created_at?: string | null;
  timestamp?: string | null;
  payload?: unknown;
};

type DataMode = "loading" | "live" | "reference" | "empty";
type PayloadRecord = Record<string, unknown>;

export function AuditEventDetailDrawer({
  auditEvent,
  dataMode,
  onClose,
}: {
  auditEvent: AuditEventSummary | null;
  dataMode: DataMode;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!auditEvent) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [auditEvent, onClose]);

  if (!auditEvent) return null;

  const payload = normalizePayload(auditEvent.payload);
  const eventId = auditEvent.audit_event_id ?? auditEvent.id ?? "No audit ID in current payload";
  const eventType = auditEvent.event_type ?? "UNKNOWN_EVENT";
  const actor = auditEvent.actor_name ?? auditEvent.actor ?? auditEvent.actor_user_id ?? "SYSTEM";
  const resourceType = auditEvent.resource_type ?? "Not included in current payload";
  const resourceId = auditEvent.resource_id ?? payloadValue(payload.record, ["resource_id", "resourceId"]) ?? "Not included in current payload";
  const sourceLabel = dataMode === "live" ? "Live API data is active" : dataMode === "reference" ? "Fallback data is active" : "Current payload state";
  const policyContext = hasPolicyContext(auditEvent, payload.preview);
  const diagnosisSessionId = payloadValue(payload.record, ["diagnosis_session_id", "diagnosisSessionId", "session_id"]) ?? resourceTraceId(resourceType, resourceId, "diagnosis_session");
  const checklistRunId = payloadValue(payload.record, ["checklist_run_id", "checklistRunId"]) ?? resourceTraceId(resourceType, resourceId, "checklist_run");
  const reportDraftId = payloadValue(payload.record, ["report_draft_id", "reportDraftId"]) ?? resourceTraceId(resourceType, resourceId, "report_draft");
  const workflowTraceReferences: WorkflowTraceReference[] = [
    {
      label: "Diagnosis Session",
      value: diagnosisSessionId,
      href: diagnosisSessionTraceHref(diagnosisSessionId),
      note: diagnosisSessionId ? "Read-only diagnosis route available" : "No linked workflow identifier is included in the current audit payload",
    },
    {
      label: "Checklist Run",
      value: checklistRunId,
      href: checklistRunTraceHref(checklistRunId),
      note: checklistRunId ? "Read-only checklist route available" : "No linked checklist in current audit payload",
    },
    {
      label: "Report Draft",
      value: reportDraftId,
      href: reportDraftTraceHref(reportDraftId),
      note: reportDraftId ? "Read-only report route available" : "No linked report in current audit payload",
      tone: "amber",
    },
    {
      label: "Agent Run",
      value: payloadValue(payload.record, ["agent_run_id", "agentRunId", "run_id"]),
      note: "No target-specific agent run route is currently available",
      tone: "slate",
    },
    {
      label: "Approval Record",
      value: payloadValue(payload.record, ["approval_id", "approvalId"]),
      note: "Approval queue is list-based in the current route set",
      tone: "slate",
    },
    {
      label: "Audit Event",
      value: eventId,
      note: "Current immutable audit record",
      tone: "slate",
    },
  ];

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50">
      <aside
        aria-label="Read-only audit event detail"
        aria-modal="true"
        role="dialog"
        className="h-full w-full max-w-xl overflow-y-auto border-l border-[#1a2c4d] bg-[#050b14] shadow-2xl shadow-black/40"
      >
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-[#1a2c4d] bg-[#050b14]/95 p-5 backdrop-blur">
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-[#00e5ff]">Read-only audit context</div>
            <div className="flex flex-wrap items-center gap-2">
              <CodePill>{eventId}</CodePill>
              <StatusBadge status={auditEvent.severity} />
            </div>
          </div>
          <button
            aria-label="Close audit event detail"
            className="rounded border border-[#1a2c4d] bg-[#0a1322] p-2 text-slate-400 transition-colors hover:border-[#00e5ff]/40 hover:text-[#00e5ff] focus:outline-none focus:ring-2 focus:ring-[#00e5ff]/40"
            type="button"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-5 p-5">
          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Database className="h-4 w-4" />} title="Audit Event Overview" />
            <div className="mt-3 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <CodePill>{eventType}</CodePill>
                <CodePill tone="slate">{resourceType}</CodePill>
              </div>
              <DetailGrid
                rows={[
                  ["Audit Event ID", eventId],
                  ["Event Type", eventType],
                  ["Severity", auditEvent.severity ?? "UNKNOWN"],
                  ["Source", sourceLabel],
                ]}
              />
            </div>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<UserRound className="h-4 w-4" />} title="Actor / Resource Context" />
            <DetailGrid
              rows={[
                ["Actor", actor],
                ["Actor Role", auditEvent.actor_role ?? "Not included in current payload"],
                ["Resource Type", resourceType],
                ["Resource ID", resourceId],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<FileJson className="h-4 w-4" />} title="Payload Detail" />
            <p className="mt-3 text-xs leading-5 text-slate-500">
              Payload is displayed as read-only audit evidence. Values are not interactive controls.
            </p>
            {payload.entries.length > 0 ? (
              <dl className="mt-3 grid grid-cols-1 gap-2 text-sm">
                {payload.entries.map(([key, value]) => (
                  <div key={key} className="min-w-0 rounded border border-[#1a2c4d] bg-[#050b14] p-3">
                    <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{key}</dt>
                    <dd className="mt-1 break-words font-mono text-xs text-slate-300">{formatPayloadValue(value)}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <pre className="mt-3 max-h-44 overflow-auto rounded border border-[#1a2c4d] bg-[#050b14] p-3 text-xs text-slate-300">
                {payload.preview}
              </pre>
            )}
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Link2 className="h-4 w-4" />} title="Workflow Traceability" />
            <WorkflowTraceList references={workflowTraceReferences} />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Clock className="h-4 w-4" />} title="Timing / Source" />
            <DetailGrid
              rows={[
                ["Timestamp", formatTimestamp(auditEvent.created_at ?? auditEvent.timestamp)],
                ["Created At", formatTimestamp(auditEvent.created_at)],
                ["Payload Format", payload.record ? "Structured key/value payload" : "Raw payload preview"],
                ["Source", sourceLabel],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<ShieldCheck className="h-4 w-4" />} title="Safety / Policy Context" />
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {policyContext
                ? "This audit record contains safety or policy context and is shown for traceability only."
                : "No explicit safety or policy marker is included in the current audit payload."}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              This panel displays immutable audit context only and does not change audit, workflow, or equipment records.
            </p>
          </section>
        </div>
      </aside>
    </div>
  );
}

function SectionTitle({ title, icon }: { title: string; icon?: ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
      {icon}
      <span>{title}</span>
    </div>
  );
}

function DetailGrid({ rows }: { rows: Array<[string, string]> }) {
  return (
    <dl className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
      {rows.map(([label, value]) => (
        <div key={label} className="min-w-0 rounded border border-[#1a2c4d] bg-[#050b14] p-3">
          <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</dt>
          <dd className="mt-1 truncate text-slate-300" title={value}>
            {value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function normalizePayload(payload: unknown): {
  preview: string;
  record: PayloadRecord | null;
  entries: Array<[string, unknown]>;
} {
  if (payload == null) {
    return { preview: "No payload included in current audit record", record: null, entries: [] };
  }

  if (typeof payload === "string") {
    const trimmed = payload.trim();
    try {
      const parsed = JSON.parse(trimmed) as unknown;
      if (isPayloadRecord(parsed)) {
        return {
          preview: JSON.stringify(parsed),
          record: parsed,
          entries: Object.entries(parsed),
        };
      }
    } catch {
      return { preview: trimmed || "No payload included in current audit record", record: null, entries: [] };
    }

    return { preview: trimmed || "No payload included in current audit record", record: null, entries: [] };
  }

  if (isPayloadRecord(payload)) {
    return {
      preview: JSON.stringify(payload),
      record: payload,
      entries: Object.entries(payload),
    };
  }

  try {
    return { preview: JSON.stringify(payload), record: null, entries: [] };
  } catch {
    return { preview: "Payload preview unavailable", record: null, entries: [] };
  }
}

function isPayloadRecord(value: unknown): value is PayloadRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function payloadValue(record: PayloadRecord | null, keys: string[]) {
  if (!record) return null;

  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
  }

  return null;
}

function resourceTraceId(resourceType: string, resourceId: string, expectedType: "diagnosis_session" | "checklist_run" | "report_draft") {
  const normalizedType = resourceType.toLowerCase().replaceAll("-", "_");
  const normalizedId = resourceId.trim();
  if (!normalizedId || normalizedId === "Not included in current payload") return null;
  return normalizedType.includes(expectedType) ? normalizedId : null;
}

function formatPayloadValue(value: unknown) {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (value == null) return "null";

  try {
    return JSON.stringify(value);
  } catch {
    return "Value preview unavailable";
  }
}

function formatTimestamp(value?: string | null) {
  if (!value) return "Not included in current payload";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not included in current payload" : date.toLocaleString();
}

function hasPolicyContext(auditEvent: AuditEventSummary, payloadPreview: string) {
  const haystack = `${auditEvent.event_type ?? ""} ${auditEvent.severity ?? ""} ${payloadPreview}`.toUpperCase();
  return haystack.includes("POLICY") || haystack.includes("SECURITY") || haystack.includes("SAFETY") || haystack.includes("BOUNDARY");
}
