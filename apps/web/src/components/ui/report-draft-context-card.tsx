"use client";

import { Clock, FileText, Link2, ShieldCheck } from "lucide-react";
import { StatusBadge } from "./operational";
import {
  WorkflowTraceList,
  checklistRunTraceHref,
  diagnosisSessionTraceHref,
  type WorkflowTraceReference,
} from "./workflow-trace";

export type ReportDraftContext = {
  id?: string | null;
  report_draft_id?: string | null;
  diagnosis_session_id?: string | null;
  agent_run_id?: string | null;
  checklist_run_id?: string | null;
  incident_id?: string | null;
  equipment_id?: string | null;
  equipment_code?: string | null;
  title?: string | null;
  status?: string | null;
  created_by_user_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  approvals?: Array<{ id?: string | null; decision?: string | null; decided_at?: string | null }>;
};

type DataMode = "loading" | "live" | "reference";

export function ReportDraftContextCard({
  report,
  dataMode,
}: {
  report: ReportDraftContext;
  dataMode: DataMode;
}) {
  const reportId = report.report_draft_id ?? report.id ?? "REPORT_UNAVAILABLE";
  const status = report.status ?? "UNKNOWN";
  const sourceLabel = dataMode === "live" ? "Live API data is active" : dataMode === "reference" ? "Fallback data is active" : "Current payload state";
  const approvals = report.approvals ?? [];
  const primaryTraceReferences: WorkflowTraceReference[] = [
    { label: "Report Draft", value: reportId, note: "Current report draft record", tone: "amber" },
    {
      label: "Diagnosis Session",
      value: report.diagnosis_session_id,
      href: diagnosisSessionTraceHref(report.diagnosis_session_id),
      note: report.diagnosis_session_id ? "Read-only detail route available" : "No diagnosis session in current payload",
    },
    {
      label: "Checklist Run",
      value: report.checklist_run_id,
      href: checklistRunTraceHref(report.checklist_run_id),
      note: report.checklist_run_id ? "Read-only detail route available" : "No linked checklist in current payload",
    },
    { label: "Agent Run", value: report.agent_run_id, note: "No target-specific route is currently available", tone: "slate" },
  ];
  const coverageReferences: WorkflowTraceReference[] = [
    { label: "Incident", value: report.incident_id, note: "No target-specific incident route is currently available", tone: "slate" },
    {
      label: "Equipment",
      value: report.equipment_code ?? report.equipment_id,
      note: "Equipment registry is list-based in the current route set",
      tone: "slate",
    },
  ];

  return (
    <section className="rounded-lg border border-[#1a2c4d] bg-[#050b14] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#00e5ff]">
            <FileText className="h-4 w-4" />
            Read-only report draft context
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Report detail is derived from the current report draft payload.
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      <div className="mt-4">
        <WorkflowTraceList references={primaryTraceReferences} />
      </div>

      <div className="mt-4 rounded border border-[#1a2c4d] bg-[#0a1322] p-3">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          <Link2 className="h-4 w-4" />
          Linked Incident / Equipment Coverage
        </div>
        <WorkflowTraceList references={coverageReferences} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <ContextCell label="Created By" value={report.created_by_user_id ?? "Creator not included in current payload"} />
        <ContextCell label="Approval Records" value={`${approvals.length} approval record${approvals.length === 1 ? "" : "s"} in payload`} />
      </div>

      <div className="mt-4 rounded border border-[#1a2c4d] bg-[#0a1322] p-3">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          <Clock className="h-4 w-4" />
          Timing / Source
        </div>
        <div className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <ContextCell label="Created" value={formatTimestamp(report.created_at)} />
          <ContextCell label="Last Updated" value={formatTimestamp(report.updated_at)} />
          <ContextCell label="Source" value={sourceLabel} />
        </div>
      </div>

      <div className="mt-4 rounded border border-[#1a2c4d] bg-[#0a1322] p-3">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          <ShieldCheck className="h-4 w-4" />
          Read-only Report Boundary
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          This panel does not generate, submit, or mutate report records.
        </p>
      </div>
    </section>
  );
}

function ContextCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded border border-[#1a2c4d] bg-[#050b14] p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-1 truncate text-slate-300" title={value}>
        {value}
      </div>
    </div>
  );
}

function formatTimestamp(value?: string | null) {
  if (!value) return "Not included in current payload";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not included in current payload" : date.toLocaleString();
}
