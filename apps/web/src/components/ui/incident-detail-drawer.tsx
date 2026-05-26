"use client";

import { useEffect, type ReactNode } from "react";
import { X, Clock, Link2, ShieldCheck } from "lucide-react";
import { CodePill, SeverityBadge, StatusBadge } from "./operational";
import {
  WorkflowTraceList,
  checklistRunTraceHref,
  diagnosisSessionTraceHref,
  reportDraftTraceHref,
  type WorkflowTraceReference,
} from "./workflow-trace";

export type IncidentSummary = {
  id?: string | null;
  incident_id?: string | null;
  case_number?: string | null;
  title?: string | null;
  summary?: string | null;
  equipment_id?: string | null;
  equipment_code?: string | null;
  tool_id?: string | null;
  area?: string | null;
  line?: string | null;
  cell?: string | null;
  alarm_code?: string | null;
  risk_level?: string | null;
  severity?: string | null;
  status?: string | null;
  opened_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  diagnosis_session_id?: string | null;
  linked_diagnosis_session_id?: string | null;
  linked_checklist_run_id?: string | null;
  checklist_run_id?: string | null;
  linked_report_draft_id?: string | null;
  report_draft_id?: string | null;
  approval_status?: string | null;
  audit_event_id?: string | null;
};

type DataMode = "loading" | "live" | "reference" | "empty";

export function IncidentDetailDrawer({
  incident,
  dataMode,
  onClose,
}: {
  incident: IncidentSummary | null;
  dataMode: DataMode;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!incident) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [incident, onClose]);

  if (!incident) return null;

  const incidentId = incident.incident_id ?? incident.id ?? incident.case_number ?? "UNKNOWN";
  const alarmCode = incident.alarm_code ?? "NO_ALARM_CODE";
  const equipmentCode = incident.equipment_code ?? incident.tool_id ?? incident.equipment_id ?? "UNKNOWN";
  const openedAt = incident.opened_at ?? incident.created_at;
  const updatedAt = incident.updated_at;
  const checklistRunId = incident.linked_checklist_run_id ?? incident.checklist_run_id;
  const reportDraftId = incident.linked_report_draft_id ?? incident.report_draft_id;
  const diagnosisSessionId = incident.linked_diagnosis_session_id ?? incident.diagnosis_session_id;
  const sourceLabel = dataMode === "live" ? "Live API data is active" : dataMode === "reference" ? "Fallback data is active" : "Current payload state";
  const equipmentTraceReferences: WorkflowTraceReference[] = [
    {
      label: "Equipment",
      value: equipmentCode,
      note: "Equipment registry is list-based in the current route set",
      tone: "slate",
    },
    {
      label: "Diagnosis Session",
      value: diagnosisSessionId,
      href: diagnosisSessionTraceHref(diagnosisSessionId),
      note: diagnosisSessionId ? "Read-only diagnosis route available" : "No linked session in current payload",
    },
  ];
  const workflowTraceReferences: WorkflowTraceReference[] = [
    {
      label: "Checklist Run",
      value: checklistRunId,
      href: checklistRunTraceHref(checklistRunId),
      note: checklistRunId ? "Read-only checklist route available" : "No linked checklist in current payload",
    },
    {
      label: "Report Draft",
      value: reportDraftId,
      href: reportDraftTraceHref(reportDraftId),
      note: reportDraftId ? "Read-only report route available" : "No linked report draft in current payload",
      tone: "amber",
    },
    {
      label: "Audit Event",
      value: incident.audit_event_id,
      note: "Audit console is list-based in the current route set",
      tone: "slate",
    },
  ];

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50">
      <aside
        aria-label="Read-only incident detail"
        aria-modal="true"
        role="dialog"
        className="h-full w-full max-w-xl overflow-y-auto border-l border-[#1a2c4d] bg-[#050b14] shadow-2xl shadow-black/40"
      >
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-[#1a2c4d] bg-[#050b14]/95 p-5 backdrop-blur">
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-[#00e5ff]">Read-only incident context</div>
            <div className="flex flex-wrap items-center gap-2">
              <CodePill>{incidentId}</CodePill>
              <SeverityBadge severity={incident.risk_level ?? incident.severity} />
              <StatusBadge status={incident.status} />
            </div>
          </div>
          <button
            aria-label="Close incident detail"
            className="rounded border border-[#1a2c4d] bg-[#0a1322] p-2 text-slate-400 transition-colors hover:border-[#00e5ff]/40 hover:text-[#00e5ff] focus:outline-none focus:ring-2 focus:ring-[#00e5ff]/40"
            type="button"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-5 p-5">
          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle title="Incident Overview" />
            <div className="mt-3 space-y-3">
              <div>
                <div className="text-sm font-semibold text-white">{incident.title ?? incident.summary ?? "Untitled incident"}</div>
                <div className="mt-2">
                  <CodePill tone="red">{alarmCode}</CodePill>
                </div>
              </div>
              <DetailGrid
                rows={[
                  ["Incident ID", incidentId],
                  ["Status", incident.status ?? "UNKNOWN"],
                  ["Severity", incident.risk_level ?? incident.severity ?? "UNKNOWN"],
                ]}
              />
            </div>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle title="Equipment Context" />
            <div className="mt-3 space-y-3">
              <WorkflowTraceList references={equipmentTraceReferences} className="mt-0" />
              <DetailGrid
                rows={[
                  ["Equipment ID", incident.equipment_id ?? "Not included in current payload"],
                  ["Area / Line / Cell", [incident.area, incident.line, incident.cell].filter(Boolean).join(" / ") || "Not included in current payload"],
                ]}
              />
            </div>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Clock className="h-4 w-4" />} title="Timing / Source" />
            <DetailGrid
              rows={[
                ["Opened", formatTimestamp(openedAt)],
                ["Last Updated", formatTimestamp(updatedAt)],
                ["Source", sourceLabel],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<ShieldCheck className="h-4 w-4" />} title="Read-only Operational Context" />
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Review checklist status, report draft context, approval trail, and audit records before any field action.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              This panel provides inspection context only and does not mutate incident, equipment, or workflow records.
            </p>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Link2 className="h-4 w-4" />} title="Related Workflow" />
            <WorkflowTraceList references={workflowTraceReferences} />
            <DetailGrid
              rows={[
                ["Approval Status", incident.approval_status ?? "No approval status in current payload"],
              ]}
            />
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

function formatTimestamp(value?: string | null) {
  if (!value) return "Not included in current payload";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not included in current payload" : date.toLocaleString();
}
