"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { CodePill, DataSourceBanner, OperationalTable, OperationalTableBody, OperationalTableHeader, StatusBadge, TableStateRow } from "@/components/ui/operational";
import { createReferenceListResponse, fetchEquipmentList } from "@/lib/api";
import { Activity, Database, AlertTriangle, ShieldCheck, Server } from "lucide-react";
import Link from "next/link";

const fallbackEquipment = [
  { id: "LP-01", equipment_code: "LP-01", equipment_name: "Load Port 01", equipment_type: "LOAD_PORT", subsystem: "FOUP Clamp", operational_status: "ALARM", current_alarm_code: "LP-CLAMP-014", risk_level: "HIGH", last_seen_at: new Date().toISOString(), linked_diagnosis_session_id: "LP-01-SESSION" },
  { id: "FC-11", equipment_code: "FC-11", equipment_name: "FOUP Clamp 11", equipment_type: "FOUP_CLAMP", subsystem: "EtherCAT I/O", operational_status: "NORMAL", current_alarm_code: null, risk_level: "LOW", last_seen_at: new Date().toISOString(), linked_diagnosis_session_id: null },
  { id: "LP-02", equipment_code: "LP-02", equipment_name: "Load Port 02", equipment_type: "LOAD_PORT", subsystem: "EtherCAT I/O", operational_status: "WARNING", current_alarm_code: "ECAT-WARN-01", risk_level: "MEDIUM", last_seen_at: new Date(Date.now() - 3600000).toISOString(), linked_diagnosis_session_id: "LP-02-SESSION" }
];

type DataMode = "loading" | "live" | "reference" | "empty";

function formatTimestamp(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

export default function EquipmentPage() {
  const [equipmentList, setEquipmentList] = useState<any[]>([]);
  const [apiTotal, setApiTotal] = useState(0);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEquipmentList()
      .then(res => {
        setEquipmentList(res.items);
        setApiTotal(res.total);
        setDataMode(res.items.length > 0 ? "live" : "empty");
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic reference data", err);
        const reference = createReferenceListResponse(fallbackEquipment);
        const message = err instanceof Error ? err.message : "Backend API unavailable";
        setEquipmentList(reference.items);
        setApiTotal(reference.total);
        setDataMode("reference");
        setError(`${message}. Showing deterministic reference data.`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const total = dataMode === "live" || dataMode === "empty" ? apiTotal : equipmentList.length;
  const inAlarm = equipmentList.filter(e => e.operational_status === 'ALARM').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Server className="w-8 h-8 text-[#00e5ff]" />
          Equipment Registry
        </h1>
        <p className="text-slate-400">
          Read-only equipment state tracking and operational scope overview.
        </p>
      </div>

      {error ? (
        <DataSourceBanner
          mode="reference"
          message={error}
          detail="Operational API connection required for live records."
        />
      ) : null}

      {dataMode === "live" ? (
        <DataSourceBanner mode="live" message="Backend API connected. Showing live read-only equipment records." />
      ) : null}

      {dataMode === "empty" ? (
        <DataSourceBanner mode="empty" message="Backend API connected. No equipment records matched the current query." />
      ) : null}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-[#050b14] border-[#1a2c4d]">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-slate-400">Total Registered</span>
              <Database className="w-4 h-4 text-slate-500" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : total}</div>
          </CardContent>
        </Card>
        <Card className="bg-[#00e5ff]/5 border-[#00e5ff]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#00e5ff]">Read-Only Operating Scope</span>
              <ShieldCheck className="w-4 h-4 text-[#00e5ff]" />
            </div>
            <div className="text-xl font-bold text-white mt-2">LP / FOUP / EtherCAT</div>
          </CardContent>
        </Card>
        <Card className="bg-[#ff3366]/5 border-[#ff3366]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#ff3366]">Active Alarms</span>
              <AlertTriangle className="w-4 h-4 text-[#ff3366]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : inAlarm}</div>
          </CardContent>
        </Card>
      </div>

      <OperationalTable>
            <OperationalTableHeader>
              <tr>
                <th className="px-4 py-3 font-medium">Equipment</th>
                <th className="px-4 py-3 font-medium">Type / Subsystem</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Current Alarm</th>
                <th className="px-4 py-3 font-medium">Last Seen</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </OperationalTableHeader>
            <OperationalTableBody>
              {loading ? (
                <TableStateRow colSpan={6} title="Loading equipment registry..." detail="Checking authenticated read-only API access." />
              ) : equipmentList.length === 0 ? (
                <TableStateRow colSpan={6} title="No equipment found in registry." detail="The live API returned an empty equipment list for this tenant." />
              ) : (
                equipmentList.map((eq, index) => {
                  const equipmentKey = eq.id ?? eq.equipment_id ?? eq.equipment_code ?? `equipment-${index}`;
                  const sessionId = eq.linked_diagnosis_session_id ?? eq.diagnosis_session_id;
                  return (
                  <tr key={equipmentKey} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <CodePill>{eq.equipment_code}</CodePill>
                      <div className="text-xs text-slate-500">{eq.equipment_name}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div>{eq.equipment_type}</div>
                      <div className="text-xs text-slate-500">{eq.subsystem}</div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={eq.operational_status} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {eq.current_alarm_code ? (
                        <CodePill tone="red">{eq.current_alarm_code}</CodePill>
                      ) : (
                        <span className="text-slate-600">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {formatTimestamp(eq.last_seen_at ?? eq.updated_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {sessionId ? (
                        <Link href={`/diagnosis-sessions/${sessionId}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#111d33] hover:bg-[#1a2c4d] border border-[#1a2c4d] text-[#00e5ff] rounded text-xs font-medium transition-colors">
                          <Activity className="w-3.5 h-3.5" />
                          View Session
                        </Link>
                      ) : (
                        <span className="text-xs text-slate-600">No Active Session</span>
                      )}
                    </td>
                  </tr>
                )})
              )}
            </OperationalTableBody>
      </OperationalTable>
    </div>
  );
}
