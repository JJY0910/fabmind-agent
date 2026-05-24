"use client";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Search, Filter, History, User, Cpu } from "lucide-react";
import { fetchAuditEvents } from "@/lib/api";
import { WorkflowStepper } from "@/components/ui/WorkflowStepper";
import {
  CodePill,
  DataSourceBanner,
  OperationalTable,
  OperationalTableBody,
  OperationalTableHeader,
  StatusBadge,
  TableStateRow,
} from "@/components/ui/operational";

const fallbackAuditEvents = [
  { id: "AE-9001", event_type: "POLICY_BLOCKED", severity: "HIGH", resource_type: "AGENT_RUN", actor: "Engineer Kim", created_at: "2026-05-16T09:45:00Z", payload: '{"request": "unsafe_action", "reason": "SAFETY_BOUNDARY"}' },
  { id: "AE-9002", event_type: "SESSION_CREATED", severity: "INFO", resource_type: "DIAGNOSIS_SESSION", actor: "Engineer Kim", created_at: "2026-05-16T08:30:00Z", payload: '{"equipment": "LP-01", "alarm": "LP-CLAMP-014"}' },
  { id: "AE-9003", event_type: "REPORT_APPROVED", severity: "INFO", resource_type: "REPORT_DRAFT", actor: "Senior Lee", created_at: "2026-05-15T15:20:00Z", payload: '{"decision": "APPROVED", "report_id": "RPT-088"}' },
  { id: "AE-9004", event_type: "LOGIN_FAILED", severity: "MEDIUM", resource_type: "AUTH", actor: "SYSTEM", created_at: "2026-05-15T10:10:00Z", payload: '{"ip": "10.0.4.15", "reason": "INVALID_CREDENTIALS"}' },
  { id: "AE-9005", event_type: "AGENT_ANALYSIS_COMPLETED", severity: "INFO", resource_type: "AGENT_RUN", actor: "SYSTEM", created_at: "2026-05-15T09:12:00Z", payload: '{"run_id": "RUN-087", "risk": "LOW"}' }
];

type DataMode = "loading" | "live" | "reference" | "empty";

function payloadPreview(payload: unknown) {
  if (typeof payload === "string") return payload;
  if (payload == null) return "{}";
  try {
    return JSON.stringify(payload);
  } catch {
    return "[unavailable]";
  }
}

function formatTimestamp(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

export default function AuditConsolePage() {
  const [auditEvents, setAuditEvents] = useState(fallbackAuditEvents);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAuditEvents()
      .then(data => {
        if (data && Array.isArray(data.items)) {
          setAuditEvents(data.items);
          setDataMode(data.items.length > 0 ? "live" : "empty");
          setError(null);
        }
      })
      .catch((err) => {
        console.warn('Backend unavailable, using deterministic reference data', err);
        const message = err instanceof Error ? err.message : "Backend API unavailable";
        setDataMode("reference");
        setError(`${message}. Showing deterministic reference data.`);
      });
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      <div className="mb-4">
        <WorkflowStepper currentStep="AUDIT" />
      </div>

      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <History className="w-8 h-8 text-[#00e5ff]" />
          Audit Console
        </h1>
        <p className="text-slate-400">
          Immutable security and system action ledger for compliance.
        </p>
      </div>

      {error ? (
        <DataSourceBanner
          mode="reference"
          message={error}
          detail="Operational API connection required for live audit event records."
        />
      ) : null}
      {dataMode === "live" ? (
        <DataSourceBanner
          mode="live"
          message={`Backend API connected. Showing ${auditEvents.length} audit event record${auditEvents.length === 1 ? "" : "s"}.`}
        />
      ) : null}
      {dataMode === "empty" ? (
        <DataSourceBanner
          mode="empty"
          message="Backend API connected. No audit events matched the current query."
        />
      ) : null}

      <Card className="overflow-hidden border-[#1a2c4d]">
        <div className="p-4 border-b border-[#1a2c4d] flex flex-col md:flex-row gap-4 justify-between bg-[#050b14]/50">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-sm group">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#00e5ff] transition-colors" />
              <input 
                type="text" 
                placeholder="Search payload or actor..." 
                className="bg-[#0a1322] border border-[#1a2c4d] rounded-md pl-9 pr-4 py-2 text-sm w-full text-slate-300 focus:outline-none focus:border-[#00e5ff] transition-colors"
              />
            </div>
            <button className="flex items-center gap-2 px-3 py-2 bg-[#0a1322] border border-[#1a2c4d] rounded-md text-sm text-slate-300 hover:bg-[#111d33] transition-colors">
              <Filter className="w-4 h-4" />
              <span>Event Type</span>
            </button>
            <button className="flex items-center gap-2 px-3 py-2 bg-[#0a1322] border border-[#1a2c4d] rounded-md text-sm text-slate-300 hover:bg-[#111d33] transition-colors">
              <Filter className="w-4 h-4" />
              <span>Severity</span>
            </button>
          </div>
          <div className="flex items-center gap-2 bg-[#0a1322] border border-[#1a2c4d] rounded-md px-3">
            <span className="text-xs text-slate-500">Showing top</span>
            <select className="bg-transparent text-sm text-slate-300 focus:outline-none py-2">
              <option value="50">50 events</option>
              <option value="100">100 events</option>
              <option value="200">200 events</option>
            </select>
          </div>
        </div>
        
        <OperationalTable>
          <OperationalTableHeader>
              <tr>
                <th className="px-6 py-3 font-semibold">Event ID / Time</th>
                <th className="px-6 py-3 font-semibold">Type & Resource</th>
                <th className="px-6 py-3 font-semibold">Severity</th>
                <th className="px-6 py-3 font-semibold">Actor</th>
                <th className="px-6 py-3 font-semibold">Payload Preview</th>
              </tr>
          </OperationalTableHeader>
          <OperationalTableBody>
              {dataMode === "loading" ? (
                <TableStateRow colSpan={5} title="Loading audit event records..." />
              ) : null}
              {dataMode === "empty" ? (
                <TableStateRow colSpan={5} title="No audit event records are currently available." />
              ) : null}
              {dataMode !== "loading" ? auditEvents.map((event) => (
                <tr key={event.id} className="hover:bg-[#111d33]/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <CodePill>{event.id}</CodePill>
                      <span className="text-[10px] text-slate-500">
                        {formatTimestamp(event.created_at)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1.5 items-start">
                      <span className="font-medium text-white text-xs">{event.event_type}</span>
                      <CodePill tone="slate">{event.resource_type}</CodePill>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={event.severity} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {(event.actor ?? 'SYSTEM') === 'SYSTEM' ? (
                        <Cpu className="w-3 h-3 text-slate-500" />
                      ) : (
                        <User className="w-3 h-3 text-slate-400" />
                      )}
                      <span className={(event.actor ?? 'SYSTEM') === 'SYSTEM' ? 'text-slate-500 font-mono text-[10px]' : 'text-slate-300 text-xs'}>
                        {event.actor ?? 'SYSTEM'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <code className="text-[10px] font-mono text-slate-400 bg-[#050b14] p-1.5 rounded border border-[#1a2c4d] block max-w-xs truncate" title={payloadPreview(event.payload)}>
                      {payloadPreview(event.payload)}
                    </code>
                  </td>
                </tr>
              )) : null}
          </OperationalTableBody>
        </OperationalTable>
      </Card>
    </div>
  );
}
