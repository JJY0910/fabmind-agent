"use client";

import { useEffect, type ReactNode } from "react";
import { Clock, FileText, Link2, ShieldCheck, UserRound, X } from "lucide-react";
import { CodePill, StatusBadge } from "./operational";
import {
  WorkflowTraceList,
  checklistRunTraceHref,
  diagnosisSessionTraceHref,
  reportDraftTraceHref,
  type WorkflowTraceReference,
} from "./workflow-trace";

export type ApprovalQueueItemSummary = {
  id?: string | null;
  approval_id?: string | null;
  report_draft_id?: string | null;
  diagnosis_session_id?: string | null;
  equipment_id?: string | null;
  equipment_code?: string | null;
  approval_status?: string | null;
  status?: string | null;
  requested_by?: string | null;
  requester_role?: string | null;
  reviewer_id?: string | null;
  reviewer_role?: string | null;
  requested_at?: string | null;
  reviewed_at?: string | null;
  updated_at?: string | null;
  reviewer_comment?: string | null;
  rejection_reason?: string | null;
  risk_level?: string | null;
  severity?: string | null;
  incident_id?: string | null;
  checklist_run_id?: string | null;
  audit_event_id?: string | null;
};

type DataMode = "loading" | "live" | "reference" | "empty";

export function ApprovalDetailDrawer({
  approval,
  currentUserRole,
  dataMode,
  onClose,
}: {
  approval: ApprovalQueueItemSummary | null;
  currentUserRole?: string | null;
  dataMode: DataMode;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!approval) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [approval, onClose]);

  if (!approval) return null;

  const approvalId = approval.approval_id ?? approval.id ?? "No approval record in current payload";
  const reportDraftId = approval.report_draft_id ?? "No linked report in current payload";
  const status = approval.approval_status ?? approval.status ?? "UNKNOWN";
  const equipmentCode = approval.equipment_code ?? approval.equipment_id ?? "Not included in current payload";
  const sourceLabel = dataMode === "live" ? "Live API data is active" : dataMode === "reference" ? "Fallback data is active" : "Current payload state";
  const workflowTraceReferences: WorkflowTraceReference[] = [
    {
      label: "Report Draft",
      value: approval.report_draft_id,
      href: reportDraftTraceHref(approval.report_draft_id),
      note: approval.report_draft_id ? "Read-only report detail route available" : "No linked report in current payload",
      tone: "amber",
    },
    {
      label: "Diagnosis Session",
      value: approval.diagnosis_session_id,
      href: diagnosisSessionTraceHref(approval.diagnosis_session_id),
      note: approval.diagnosis_session_id ? "Read-only diagnosis route available" : "No linked workflow record in current payload",
    },
    {
      label: "Checklist Run",
      value: approval.checklist_run_id,
      href: checklistRunTraceHref(approval.checklist_run_id),
      note: approval.checklist_run_id ? "Read-only checklist route available" : "No linked checklist in current payload",
    },
    { label: "Incident", value: approval.incident_id, note: "No target-specific incident route is currently available", tone: "slate" },
    { label: "Approval Record", value: approvalId, note: "Approval queue is list-based in the current route set", tone: "slate" },
    { label: "Audit Event", value: approval.audit_event_id, note: "Audit console is list-based in the current route set", tone: "slate" },
  ];

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50">
      <aside
        aria-label="Read-only approval detail"
        aria-modal="true"
        role="dialog"
        className="h-full w-full max-w-xl overflow-y-auto border-l border-[#1a2c4d] bg-[#050b14] shadow-2xl shadow-black/40"
      >
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-[#1a2c4d] bg-[#050b14]/95 p-5 backdrop-blur">
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-[#ffaa00]">Read-only approval context</div>
            <div className="flex flex-wrap items-center gap-2">
              <CodePill tone="amber">{reportDraftId}</CodePill>
              <StatusBadge status={status} />
            </div>
          </div>
          <button
            aria-label="Close approval detail"
            className="rounded border border-[#1a2c4d] bg-[#0a1322] p-2 text-slate-400 transition-colors hover:border-[#ffaa00]/40 hover:text-[#ffaa00] focus:outline-none focus:ring-2 focus:ring-[#ffaa00]/40"
            type="button"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-5 p-5">
          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<FileText className="h-4 w-4" />} title="Approval Overview" />
            <div className="mt-3 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <CodePill tone="amber">{approvalId}</CodePill>
                <CodePill>{equipmentCode}</CodePill>
              </div>
              <DetailGrid
                rows={[
                  ["Report Draft", reportDraftId],
                  ["Status", status],
                  ["Review Requirement", approval.reviewer_role ?? "Senior engineer or admin review"],
                  ["Equipment", equipmentCode],
                ]}
              />
            </div>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<UserRound className="h-4 w-4" />} title="Request Context" />
            <DetailGrid
              rows={[
                ["Requester", approval.requested_by ?? "Requester not included in current payload"],
                ["Requested At", formatTimestamp(approval.requested_at)],
                ["Requester Role", approval.requester_role ?? "Not included in current payload"],
                ["Current User Role", currentUserRole ?? "Role unavailable in current session"],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Link2 className="h-4 w-4" />} title="Report / Workflow Context" />
            <WorkflowTraceList references={workflowTraceReferences} />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle title="Risk / Review Signals" />
            <DetailGrid
              rows={[
                ["Risk Level", approval.risk_level ?? approval.severity ?? "Not included in current payload"],
                ["Reviewer", approval.reviewer_id ?? "No reviewer recorded in current payload"],
                ["Reviewer Note", approval.reviewer_comment ?? "No reviewer note in current payload"],
                ["Rejection Reason", approval.rejection_reason ?? "No rejection reason in current payload"],
              ]}
            />
            <p className="mt-3 text-xs text-slate-500">Risk and review signals are shown only when they are present in the current payload.</p>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Clock className="h-4 w-4" />} title="Timing / Source" />
            <DetailGrid
              rows={[
                ["Requested", formatTimestamp(approval.requested_at)],
                ["Reviewed", formatTimestamp(approval.reviewed_at)],
                ["Last Updated", formatTimestamp(approval.updated_at)],
                ["Source", sourceLabel],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<ShieldCheck className="h-4 w-4" />} title="Read-only Review Boundary" />
            <p className="mt-3 text-sm leading-6 text-slate-300">
              This panel provides review context only and does not approve, reject, or mutate report records.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Decision action is not available in this read-only panel.
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

function formatTimestamp(value?: string | null) {
  if (!value) return "Not included in current payload";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not included in current payload" : date.toLocaleString();
}
