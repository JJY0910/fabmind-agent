"use client";

import { useEffect, type ReactNode } from "react";
import { CheckCircle2, Clock, Link2, ShieldCheck, X } from "lucide-react";
import { CodePill, StatusBadge } from "./operational";
import {
  WorkflowTraceList,
  diagnosisSessionTraceHref,
  reportDraftTraceHref,
  type WorkflowTraceReference,
} from "./workflow-trace";

export type ChecklistRunSummary = {
  id?: string | null;
  checklist_run_id?: string | null;
  diagnosis_session_id?: string | null;
  equipment_id?: string | null;
  equipment_code?: string | null;
  checklist_name?: string | null;
  status?: string | null;
  total_items?: number | string | null;
  completed_items?: number | string | null;
  failed_items?: number | string | null;
  pending_items?: number | string | null;
  created_at?: string | null;
  updated_at?: string | null;
  report_draft_id?: string | null;
  linked_report_draft_id?: string | null;
  approval_status?: string | null;
  audit_event_id?: string | null;
};

type DataMode = "loading" | "live" | "reference" | "empty";
type StepState = "complete" | "current" | "pending";

const STEP_LABELS = ["Registered", "In Progress", "Review Ready", "Completed"];

export function ChecklistRunDetailDrawer({
  checklistRun,
  dataMode,
  onClose,
}: {
  checklistRun: ChecklistRunSummary | null;
  dataMode: DataMode;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!checklistRun) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [checklistRun, onClose]);

  if (!checklistRun) return null;

  const runId = checklistRun.checklist_run_id ?? checklistRun.id ?? "UNKNOWN";
  const totalItems = toCount(checklistRun.total_items);
  const completedItems = toCount(checklistRun.completed_items);
  const failedItems = toCount(checklistRun.failed_items);
  const pendingItems = toCount(checklistRun.pending_items);
  const progressPercent = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
  const reportDraftId = checklistRun.linked_report_draft_id ?? checklistRun.report_draft_id;
  const sourceLabel = dataMode === "live" ? "Live API data is active" : dataMode === "reference" ? "Fallback data is active" : "Current payload state";
  const steps = deriveSteps(checklistRun.status, completedItems, totalItems, failedItems);
  const contextTraceReferences: WorkflowTraceReference[] = [
    {
      label: "Diagnosis Session",
      value: checklistRun.diagnosis_session_id,
      href: diagnosisSessionTraceHref(checklistRun.diagnosis_session_id),
      note: checklistRun.diagnosis_session_id ? "Read-only diagnosis route available" : "No linked session in current payload",
    },
    {
      label: "Equipment",
      value: checklistRun.equipment_code ?? checklistRun.equipment_id,
      note: "Equipment registry is list-based in the current route set",
      tone: "slate",
    },
  ];
  const workflowTraceReferences: WorkflowTraceReference[] = [
    {
      label: "Report Draft",
      value: reportDraftId,
      href: reportDraftTraceHref(reportDraftId),
      note: reportDraftId ? "Read-only report route available" : "No linked report in current payload",
      tone: "amber",
    },
    {
      label: "Audit Event",
      value: checklistRun.audit_event_id,
      note: "Audit console is list-based in the current route set",
      tone: "slate",
    },
  ];

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50">
      <aside
        aria-label="Read-only checklist run detail"
        aria-modal="true"
        role="dialog"
        className="h-full w-full max-w-xl overflow-y-auto border-l border-[#1a2c4d] bg-[#050b14] shadow-2xl shadow-black/40"
      >
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-[#1a2c4d] bg-[#050b14]/95 p-5 backdrop-blur">
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-[#00e5ff]">Read-only checklist run context</div>
            <div className="flex flex-wrap items-center gap-2">
              <CodePill>{runId}</CodePill>
              <StatusBadge status={checklistRun.status} />
            </div>
          </div>
          <button
            aria-label="Close checklist run detail"
            className="rounded border border-[#1a2c4d] bg-[#0a1322] p-2 text-slate-400 transition-colors hover:border-[#00e5ff]/40 hover:text-[#00e5ff] focus:outline-none focus:ring-2 focus:ring-[#00e5ff]/40"
            type="button"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-5 p-5">
          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle title="Checklist Run Overview" />
            <div className="mt-3 space-y-4">
              <div>
                <div className="text-sm font-semibold text-white">{checklistRun.checklist_name ?? "Unnamed checklist run"}</div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <CodePill>{checklistRun.equipment_code ?? checklistRun.equipment_id ?? "UNKNOWN"}</CodePill>
                  <span className="text-xs text-slate-500">{progressPercent}% complete</span>
                </div>
              </div>
              <ProgressBar completedItems={completedItems} totalItems={totalItems} />
              <DetailGrid
                rows={[
                  ["Run ID", runId],
                  ["Status", checklistRun.status ?? "UNKNOWN"],
                  ["Progress", `${completedItems}/${totalItems} items`],
                  ["Blocked Items", String(failedItems)],
                ]}
              />
            </div>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle title="Equipment / Session Context" />
            <WorkflowTraceList references={contextTraceReferences} />
            <DetailGrid
              rows={[
                ["Pending Items", String(pendingItems)],
                ["Source", sourceLabel],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<CheckCircle2 className="h-4 w-4" />} title="Stepper / Progress" />
            <ol className="mt-4 space-y-3">
              {steps.map((step, index) => (
                <li key={step.label} className="flex gap-3">
                  <span className={stepIndicatorClass(step.state)}>{index + 1}</span>
                  <div>
                    <div className={step.state === "pending" ? "text-sm font-medium text-slate-500" : "text-sm font-medium text-white"}>
                      {step.label}
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">{step.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
            <p className="mt-4 text-xs text-slate-500">Step progress is derived from the current read-only payload.</p>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Clock className="h-4 w-4" />} title="Timing / Source" />
            <DetailGrid
              rows={[
                ["Created", formatTimestamp(checklistRun.created_at)],
                ["Last Updated", formatTimestamp(checklistRun.updated_at)],
                ["Data Mode", sourceLabel],
              ]}
            />
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<ShieldCheck className="h-4 w-4" />} title="Read-only Operational Context" />
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Review checklist progress, linked report context, approval trail, and audit records before workflow handoff.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              This panel provides inspection context only and does not mutate checklist, equipment, or workflow records.
            </p>
          </section>

          <section className="rounded-lg border border-[#1a2c4d] bg-[#0a1322] p-4">
            <SectionTitle icon={<Link2 className="h-4 w-4" />} title="Related Workflow" />
            <WorkflowTraceList references={workflowTraceReferences} />
            <DetailGrid
              rows={[
                ["Approval Status", checklistRun.approval_status ?? "No approval status in current read-only payload"],
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

function ProgressBar({ completedItems, totalItems }: { completedItems: number; totalItems: number }) {
  const progress = totalItems > 0 ? Math.min(100, Math.round((completedItems / totalItems) * 100)) : 0;
  return (
    <div className="space-y-2">
      <div className="h-2 overflow-hidden rounded-full bg-[#111d33]">
        <div className="h-2 rounded-full bg-[#00cc66]" style={{ width: `${progress}%` }} />
      </div>
      <div className="text-xs text-slate-500">
        {completedItems}/{totalItems} checklist items complete
      </div>
    </div>
  );
}

function deriveSteps(status?: string | null, completedItems = 0, totalItems = 0, failedItems = 0) {
  const normalized = (status ?? "").toUpperCase();
  const hasStarted = normalized !== "CREATED" || completedItems > 0;
  const reviewReady = totalItems > 0 && completedItems + failedItems >= totalItems && normalized !== "COMPLETED";
  const completed = normalized === "COMPLETED";

  return STEP_LABELS.map((label) => {
    if (label === "Registered") {
      return { label, state: "complete" as StepState, detail: "Checklist run is present in the current payload." };
    }
    if (label === "In Progress") {
      return {
        label,
        state: completed || reviewReady ? "complete" as StepState : hasStarted ? "current" as StepState : "pending" as StepState,
        detail: "Checklist item progress is visible for operational review.",
      };
    }
    if (label === "Review Ready") {
      return {
        label,
        state: completed ? "complete" as StepState : reviewReady ? "current" as StepState : "pending" as StepState,
        detail: "Review readiness is inferred only when item counts support it.",
      };
    }
    return {
      label,
      state: completed ? "complete" as StepState : "pending" as StepState,
      detail: "Completion is shown only when the run status reports completed.",
    };
  });
}

function stepIndicatorClass(state: StepState) {
  if (state === "complete") return "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[#00cc66]/40 bg-[#00cc66]/10 text-xs font-bold text-[#00cc66]";
  if (state === "current") return "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[#00e5ff]/40 bg-[#00e5ff]/10 text-xs font-bold text-[#00e5ff]";
  return "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[#1a2c4d] bg-[#050b14] text-xs font-bold text-slate-500";
}

function toCount(value?: number | string | null) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatTimestamp(value?: string | null) {
  if (!value) return "Not included in current payload";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not included in current payload" : date.toLocaleString();
}
