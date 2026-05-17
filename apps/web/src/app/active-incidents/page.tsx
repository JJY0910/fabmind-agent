"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createReferenceListResponse, fetchIncidentList } from "@/lib/api";
import { ShieldAlert, AlertTriangle, ChevronRight, CheckSquare, FileText, Clock } from "lucide-react";
import Link from "next/link";

const fallbackIncidents = [
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
  const [incidents, setIncidents] = useState<any[]>([]);
  const [apiTotal, setApiTotal] = useState(0);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchIncidentList()
      .then(res => {
        setIncidents(res.items);
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

  const totalOpen = incidents.filter(i => ACTIVE_STATUSES.has(i.status)).length;
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

      {error && (
        <div className="bg-[#ffaa00]/10 border border-[#ffaa00]/30 text-[#ffaa00] p-3 rounded-md text-sm mb-4">
          {error}
          <span className="block text-xs text-[#ffaa00]/80 mt-1">Operational API connection required for live incident records.</span>
        </div>
      )}

      {dataMode === "live" && (
        <div className="bg-[#00cc66]/10 border border-[#00cc66]/30 text-[#00cc66] p-3 rounded-md text-sm mb-4">
          Backend API connected. Showing {apiTotal} tenant-scoped incident record{apiTotal === 1 ? "" : "s"}.
        </div>
      )}

      {dataMode === "empty" && (
        <div className="bg-[#111d33] border border-[#1a2c4d] text-slate-300 p-3 rounded-md text-sm mb-4">
          Backend API connected. No active incidents matched the current query.
        </div>
      )}

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

      {/* Incidents Table */}
      <Card className="border-[#1a2c4d] overflow-hidden bg-[#0a1322]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-[#111d33] border-b border-[#1a2c4d] text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Incident / Alarm</th>
                <th className="px-4 py-3 font-medium">Equipment</th>
                <th className="px-4 py-3 font-medium">Status / Severity</th>
                <th className="px-4 py-3 font-medium">Links</th>
                <th className="px-4 py-3 font-medium">Opened At</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a2c4d]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading incidents...</td>
                </tr>
              ) : incidents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No active incidents found.</td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr key={inc.incident_id ?? inc.id} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{inc.title}</div>
                      <div className="font-mono text-[#ff3366] text-xs mt-0.5">{inc.alarm_code}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-[#00e5ff] text-xs bg-[#00e5ff]/10 px-2 py-0.5 rounded border border-[#00e5ff]/20">{inc.equipment_code}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1.5 items-start">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                          inc.status === 'CHECKLIST_IN_PROGRESS' || inc.status === 'TRIAGED' ? 'bg-[#00e5ff]/10 text-[#00e5ff] border-[#00e5ff]/30' :
                          'bg-[#ffaa00]/10 text-[#ffaa00] border-[#ffaa00]/30'
                        }`}>
                          {inc.status}
                        </span>
                        <span className={`text-[10px] font-bold ${(inc.risk_level ?? inc.severity) === 'HIGH' ? 'text-[#ff3366]' : 'text-[#ffaa00]'}`}>
                          {inc.risk_level ?? inc.severity ?? "UNKNOWN"} SEVERITY
                        </span>
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
                      {(inc.diagnosis_session_id ?? inc.linked_diagnosis_session_id) ? (
                        <Link href={`/diagnosis-sessions/${inc.diagnosis_session_id ?? inc.linked_diagnosis_session_id}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#00e5ff] hover:bg-[#00e5ff]/90 text-black rounded text-xs font-bold transition-colors shadow-[0_0_10px_rgba(0,229,255,0.2)]">
                          Triage
                        </Link>
                      ) : (
                        <span className="text-xs text-slate-600">No linked session</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
