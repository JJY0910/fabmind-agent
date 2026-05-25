"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { IncidentDetailDrawer, type IncidentSummary } from "@/components/ui/incident-detail-drawer";
import { CodePill, DataSourceBanner, OperationalTable, OperationalTableBody, OperationalTableHeader, SeverityBadge, StatusBadge, TableStateRow } from "@/components/ui/operational";
import { createReferenceListResponse, fetchIncidentList } from "@/lib/api";
import { ShieldAlert, AlertTriangle, CheckSquare, FileText, Clock } from "lucide-react";
import Link from "next/link";

const fallbackIncidents: IncidentSummary[] = [
  { incident_id: "INC-LP-01", equipment_code: "LP-01", alarm_code: "LP-CLAMP-014", title: "Clamp Sensor Misalignment", risk_level: "HIGH", status: "CHECKLIST_IN_PROGRESS", opened_at: new Date(Date.now() - 3600000).toISOString(), updated_at: new Date(Date.now() - 1800000).toISOString(), diagnosis_session_id: "LP-01-SESSION", linked_checklist_run_id: "RUN-LP-01", linked_report_draft_id: "RPT-LP-01" },
  { incident_id: "INC-LP-02", equipment_code: "LP-02", alarm_code: "ECAT-STATE-021", title: "EtherCAT Slave PRE-OP Lock", risk_level: "HIGH", status: "OPEN", opened_at: new Date(Date.now() - 7200000).toISOString(), updated_at: new Date(Date.now() - 7000000).toISOString(), diagnosis_session_id: "LP-02-SESSION", linked_checklist_run_id: null, linked_report_draft_id: null },
];

type DataMode = "loading" | "live" | "reference" | "empty";
const ACTIVE_STATUSES = new Set(["OPEN", "TRIAGED", "CHECKLIST_IN_PROGRESS", "REPORT_SUBMITTED"]);

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleDateString();
}

function formatTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString();
}

export default function ActiveIncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentSummary | null>(null);
  const [apiTotal, setApiTotal] = useState(0);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchIncidentList()
      .then(res => {
        setIncidents(res.items as IncidentSummary[]);
        setApiTotal(res.total);
        setDataMode(res.items.length > 0 ? "live" : "empty");
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic reference data", err);
        const reference = createReferenceListResponse(fallbackIncidents);
        const message = err instanceof Error ? err.message : "Backend API unavailable";
        setIncidents(reference.items);
        setApiTotal(reference.total);
        setDataMode("reference");
        setError(`${message}. Showing deterministic reference data.`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const totalOpen = incidents.filter(i => ACTIVE_STATUSES.has(i.status ?? "")).length;
  const highRisk = incidents.filter(i => (i.risk_level ?? i.severity) === 'HIGH').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <ShieldAlert className="w-8 h-8 text-[#ff3366]" />
          Active Incidents
        </h1>
        <p className="text-slate-400">
          Track active equipment alarms and triage states.
        </p>
      </div>

      {error ? (
        <DataSourceBanner
          mode="reference"
          message={error}
          detail="Operational API connection required for live incident records."
        />
      ) : null}

      {dataMode === "live" ? (
        <DataSourceBanner mode="live" message={`Backend API connected. Showing ${apiTotal} tenant-scoped incident record${apiTotal === 1 ? "" : "s"}.`} />
      ) : null}

      {dataMode === "empty" ? (
        <DataSourceBanner mode="empty" message="Backend API connected. No active incidents matched the current query." />
      ) : null}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-[#050b14] border-[#1a2c4d]">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-slate-400">Open Incidents</span>
              <ShieldAlert className="w-4 h-4 text-[#ffaa00]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : totalOpen}</div>
          </CardContent>
        </Card>
        <Card className="bg-[#ff3366]/5 border-[#ff3366]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#ff3366]">High Severity</span>
              <AlertTriangle className="w-4 h-4 text-[#ff3366]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : highRisk}</div>
          </CardContent>
        </Card>
      </div>

      <OperationalTable>
            <OperationalTableHeader>
              <tr>
                <th className="px-4 py-3 font-medium">Incident / Alarm</th>
                <th className="px-4 py-3 font-medium">Equipment</th>
                <th className="px-4 py-3 font-medium">Status / Severity</th>
                <th className="px-4 py-3 font-medium">Links</th>
                <th className="px-4 py-3 font-medium">Opened At</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </OperationalTableHeader>
            <OperationalTableBody>
              {loading ? (
                <TableStateRow colSpan={6} title="Loading incidents..." detail="Checking authenticated read-only API access." />
              ) : incidents.length === 0 ? (
                <TableStateRow colSpan={6} title="No active incidents found." detail="The live API returned no open or triaged incident records." />
              ) : (
                incidents.map((inc) => (
                  <tr key={inc.incident_id ?? inc.id} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{inc.title}</div>
                      <CodePill tone="red" className="mt-1">{inc.alarm_code}</CodePill>
                    </td>
                    <td className="px-4 py-3">
                      <CodePill>{inc.equipment_code}</CodePill>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1.5 items-start">
                        <StatusBadge status={inc.status} />
                        <SeverityBadge severity={inc.risk_level ?? inc.severity} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {inc.linked_checklist_run_id && <span title="Checklist Linked"><CheckSquare className="w-4 h-4 text-[#00cc66]" /></span>}
                        {inc.linked_report_draft_id && <span title="Report Draft Linked"><FileText className="w-4 h-4 text-[#ffaa00]" /></span>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      <div className="flex items-center gap-1"><Clock className="w-3 h-3" /> {formatDate(inc.opened_at)}</div>
                      <div className="text-slate-600 ml-4">{formatTime(inc.opened_at)}</div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 rounded border border-[#1a2c4d] bg-[#111d33] px-3 py-1.5 text-xs font-medium text-[#00e5ff] transition-colors hover:border-[#00e5ff]/40 hover:bg-[#1a2c4d] focus:outline-none focus:ring-2 focus:ring-[#00e5ff]/40"
                          aria-label={`Inspect incident ${inc.incident_id ?? inc.id ?? "detail"}`}
                          onClick={() => setSelectedIncident(inc)}
                        >
                          Inspect
                        </button>
                        {(inc.diagnosis_session_id ?? inc.linked_diagnosis_session_id) ? (
                          <Link href={`/diagnosis-sessions/${inc.diagnosis_session_id ?? inc.linked_diagnosis_session_id}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#00e5ff] hover:bg-[#00e5ff]/90 text-black rounded text-xs font-bold transition-colors shadow-[0_0_10px_rgba(0,229,255,0.2)]">
                            Triage
                          </Link>
                        ) : (
                          <span className="text-xs text-slate-600">No linked session</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </OperationalTableBody>
      </OperationalTable>

      <IncidentDetailDrawer
        dataMode={dataMode}
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
      />
    </div>
  );
}
