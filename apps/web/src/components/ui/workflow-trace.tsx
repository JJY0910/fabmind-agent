"use client";

import Link from "next/link";

import { cn } from "./card";

type Tone = "cyan" | "green" | "amber" | "red" | "slate";

export type WorkflowTraceReference = {
  label: string;
  value?: string | null;
  href?: string;
  note?: string;
  tone?: Tone;
};

const toneClasses: Record<Tone, string> = {
  cyan: "border-[#00e5ff]/30 bg-[#00e5ff]/10 text-[#00e5ff]",
  green: "border-[#00cc66]/30 bg-[#00cc66]/10 text-[#00cc66]",
  amber: "border-[#ffaa00]/30 bg-[#ffaa00]/10 text-[#ffaa00]",
  red: "border-[#ff3366]/30 bg-[#ff3366]/10 text-[#ff3366]",
  slate: "border-[#1a2c4d] bg-[#050b14] text-slate-400",
};

const linkClasses =
  "inline-flex w-fit max-w-full items-center rounded border px-2 py-0.5 font-mono text-xs transition-colors hover:border-[#00e5ff]/60 hover:bg-[#00e5ff]/15 focus:outline-none focus:ring-2 focus:ring-[#00e5ff]/40";

const pillClasses = "inline-flex w-fit max-w-full items-center rounded border px-2 py-0.5 font-mono text-xs";

export function WorkflowTraceList({
  references,
  className,
}: {
  references: WorkflowTraceReference[];
  className?: string;
}) {
  return (
    <dl className={cn("mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2", className)}>
      {references.map((reference) => (
        <WorkflowTraceItem key={reference.label} reference={reference} />
      ))}
    </dl>
  );
}

function WorkflowTraceItem({ reference }: { reference: WorkflowTraceReference }) {
  const tone = reference.tone ?? "cyan";
  const value = normalizeTraceValue(reference.value);
  const isLinked = Boolean(reference.href && hasTraceValue(reference.value));

  return (
    <div className="min-w-0 rounded border border-[#1a2c4d] bg-[#050b14] p-3">
      <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{reference.label}</dt>
      <dd className="mt-1 min-w-0">
        {isLinked ? (
          <Link
            href={reference.href as string}
            aria-label={`View read-only ${reference.label} ${value}`}
            className={cn(linkClasses, toneClasses[tone])}
            title={value}
          >
            <span className="truncate">{value}</span>
          </Link>
        ) : (
          <span className={cn(pillClasses, toneClasses[tone])} title={value}>
            <span className="truncate">{value}</span>
          </span>
        )}
        {reference.note ? <div className="mt-1 text-[11px] leading-4 text-slate-500">{reference.note}</div> : null}
      </dd>
    </div>
  );
}

export function reportDraftTraceHref(value?: string | null) {
  return traceHref("report-drafts", value);
}

export function checklistRunTraceHref(value?: string | null) {
  return traceHref("checklist-runs", value);
}

export function diagnosisSessionTraceHref(value?: string | null) {
  return traceHref("diagnosis-sessions", value);
}

function traceHref(routeSegment: "report-drafts" | "checklist-runs" | "diagnosis-sessions", value?: string | null) {
  const normalizedValue = value?.trim();
  if (!normalizedValue) return undefined;
  return `/${routeSegment}/${encodeURIComponent(normalizedValue)}`;
}

function hasTraceValue(value?: string | null) {
  return Boolean(value && value.trim());
}

function normalizeTraceValue(value?: string | null) {
  return hasTraceValue(value) ? value!.trim() : "Not included in current payload";
}
