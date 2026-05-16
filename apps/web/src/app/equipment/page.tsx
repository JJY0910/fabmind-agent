"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchEquipmentList } from "@/lib/api";
import { Activity, Database, AlertTriangle, ShieldCheck, ChevronRight, Server } from "lucide-react";
import Link from "next/link";

const fallbackEquipment = [
  { id: "LP-01", equipment_code: "LP-01", equipment_name: "Load Port 01", equipment_type: "LOAD_PORT", subsystem: "FOUP Clamp", operational_status: "ALARM", current_alarm_code: "LP-CLAMP-014", risk_level: "HIGH", updated_at: new Date().toISOString(), linked_diagnosis_session_id: "LP-01-SESSION" },
  { id: "FC-11", equipment_code: "FC-11", equipment_name: "FOUP Clamp 11", equipment_type: "FOUP_CLAMP", subsystem: "EtherCAT I/O", operational_status: "NORMAL", current_alarm_code: null, risk_level: "LOW", updated_at: new Date().toISOString(), linked_diagnosis_session_id: null },
  { id: "LP-02", equipment_code: "LP-02", equipment_name: "Load Port 02", equipment_type: "LOAD_PORT", subsystem: "EtherCAT I/O", operational_status: "WARNING", current_alarm_code: "ECAT-WARN-01", risk_level: "MEDIUM", updated_at: new Date(Date.now() - 3600000).toISOString(), linked_diagnosis_session_id: "LP-02-SESSION" }
];

export default function EquipmentPage() {
  const [equipmentList, setEquipmentList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEquipmentList()
      .then(res => {
        if (res && res.data && Array.isArray(res.data)) {
          setEquipmentList(res.data);
        } else if (Array.isArray(res)) {
          setEquipmentList(res);
        } else {
          setEquipmentList(fallbackEquipment);
        }
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic fallback fixture", err);
        setEquipmentList(fallbackEquipment);
        setError("Backend API unavailable. Displaying deterministic fallback fixture.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const total = equipmentList.length;
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

      {error && (
        <div className="bg-[#ffaa00]/10 border border-[#ffaa00]/30 text-[#ffaa00] p-3 rounded-md text-sm mb-4">
          {error}
        </div>
      )}

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

      {/* Equipment Table */}
      <Card className="border-[#1a2c4d] overflow-hidden bg-[#0a1322]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-[#111d33] border-b border-[#1a2c4d] text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Equipment</th>
                <th className="px-4 py-3 font-medium">Type / Subsystem</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Current Alarm</th>
                <th className="px-4 py-3 font-medium">Last Seen</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a2c4d]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading equipment registry...</td>
                </tr>
              ) : equipmentList.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No equipment found in registry.</td>
                </tr>
              ) : (
                equipmentList.map((eq) => (
                  <tr key={eq.id} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-mono text-[#00e5ff] font-medium">{eq.equipment_code}</div>
                      <div className="text-xs text-slate-500">{eq.equipment_name}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div>{eq.equipment_type}</div>
                      <div className="text-xs text-slate-500">{eq.subsystem}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                        eq.operational_status === 'ALARM' ? 'bg-[#ff3366]/10 text-[#ff3366] border-[#ff3366]/30' :
                        eq.operational_status === 'WARNING' ? 'bg-[#ffaa00]/10 text-[#ffaa00] border-[#ffaa00]/30' :
                        'bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30'
                      }`}>
                        {eq.operational_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {eq.current_alarm_code ? (
                        <span className="text-[#ff3366]">{eq.current_alarm_code}</span>
                      ) : (
                        <span className="text-slate-600">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(eq.updated_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {eq.linked_diagnosis_session_id ? (
                        <Link href={`/diagnosis-sessions/${eq.linked_diagnosis_session_id}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#111d33] hover:bg-[#1a2c4d] border border-[#1a2c4d] text-[#00e5ff] rounded text-xs font-medium transition-colors">
                          <Activity className="w-3.5 h-3.5" />
                          View Session
                        </Link>
                      ) : (
                        <span className="text-xs text-slate-600">No Active Session</span>
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
