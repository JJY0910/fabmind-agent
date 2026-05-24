import * as React from "react";

import { cn } from "./card";

type Tone = "cyan" | "green" | "amber" | "red" | "slate";
type DataMode = "loading" | "live" | "reference" | "empty";

const toneClasses: Record<Tone, string> = {
  cyan: "border-[#00e5ff]/30 bg-[#00e5ff]/10 text-[#00e5ff]",
  green: "border-[#00cc66]/30 bg-[#00cc66]/10 text-[#00cc66]",
  amber: "border-[#ffaa00]/30 bg-[#ffaa00]/10 text-[#ffaa00]",
  red: "border-[#ff3366]/30 bg-[#ff3366]/10 text-[#ff3366]",
  slate: "border-[#1a2c4d] bg-[#050b14] text-slate-400",
};

const toneTextClasses: Record<Tone, string> = {
  cyan: "text-[#00e5ff]",
  green: "text-[#00cc66]",
  amber: "text-[#ffaa00]",
  red: "text-[#ff3366]",
  slate: "text-slate-500",
};

function formatLabel(value?: string | null) {
  return (value ?? "UNKNOWN").replaceAll("_", " ");
}

function statusTone(status?: string | null): Tone {
  switch ((status ?? "").toUpperCase()) {
    case "NORMAL":
    case "COMPLETED":
    case "APPROVED":
    case "CLOSED":
      return "green";
    case "ALARM":
    case "HIGH":
    case "ERROR":
    case "SECURITY":
    case "REJECTED":
      return "red";
    case "WARNING":
    case "MEDIUM":
    case "OPEN":
    case "PENDING_REVIEW":
    case "SUBMITTED":
      return "amber";
    case "TRIAGED":
    case "IN_PROGRESS":
    case "CHECKLIST_IN_PROGRESS":
    case "REPORT_SUBMITTED":
    case "ANALYSIS_READY":
      return "cyan";
    default:
      return "slate";
  }
}

export function StatusBadge({ status, className }: { status?: string | null; className?: string }) {
  const tone = statusTone(status);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
        toneClasses[tone],
        className,
      )}
    >
      {formatLabel(status)}
    </span>
  );
}

export function SeverityBadge({ severity, className }: { severity?: string | null; className?: string }) {
  const tone = statusTone(severity);
  return (
    <span className={cn("text-[10px] font-bold uppercase tracking-wider", toneTextClasses[tone], className)}>
      {formatLabel(severity)} severity
    </span>
  );
}

export function CodePill({
  children,
  tone = "cyan",
  className,
}: {
  children: React.ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex w-fit items-center rounded border px-2 py-0.5 font-mono text-xs", toneClasses[tone], className)}>
      {children}
    </span>
  );
}

export function DataSourceBanner({
  mode,
  message,
  detail,
}: {
  mode: DataMode;
  message: string;
  detail?: string;
}) {
  if (mode === "loading") return null;

  const tone: Tone = mode === "live" ? "green" : mode === "reference" ? "amber" : "slate";

  return (
    <div className={cn("rounded-lg border p-3 text-sm", toneClasses[tone])}>
      <span>{message}</span>
      {detail ? <span className="mt-1 block text-xs opacity-80">{detail}</span> : null}
    </div>
  );
}

export function OperationalTable({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-lg border border-[#1a2c4d] bg-[#0a1322]", className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">{children}</table>
      </div>
    </div>
  );
}

export function OperationalTableHeader({ children }: { children: React.ReactNode }) {
  return (
    <thead className="border-b border-[#1a2c4d] bg-[#111d33] text-xs uppercase tracking-wide text-slate-400">
      {children}
    </thead>
  );
}

export function OperationalTableBody({ children }: { children: React.ReactNode }) {
  return <tbody className="divide-y divide-[#1a2c4d]">{children}</tbody>;
}

export function TableStateRow({
  colSpan,
  title,
  detail,
}: {
  colSpan: number;
  title: string;
  detail?: string;
}) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-9 text-center">
        <div className="text-sm font-medium text-slate-400">{title}</div>
        {detail ? <div className="mt-1 text-xs text-slate-600">{detail}</div> : null}
      </td>
    </tr>
  );
}
