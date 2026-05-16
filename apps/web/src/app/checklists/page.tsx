"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchChecklistRunList } from "@/lib/api";
import { CheckSquare, CheckCircle2, Clock, ShieldAlert, FileText, Activity } from "lucide-react";
import Link from "next/link";

const fallbackChecklists = [
  { id: "RUN-LP-01", diagnosis_session_id: "LP-01-SESSION", equipment_code: "LP-01", checklist_name: "FOUP Clamp Sensor Misalignment Check", status: "IN_PROGRESS", total_items: 3, completed_items: 1, failed_items: 0, pending_items: 2, created_at: new Date(Date.now() - 3600000).toISOString(), updated_at: new Date(Date.now() - 1800000).toISOString() },
  { id: "RUN-FC-11", diagnosis_session_id: "FC-11-SESSION", equipment_code: "FC-11", checklist_name: "EtherCAT Slave Status Check", status: "COMPLETED", total_items: 5, completed_items: 5, failed_items: 0, pending_items: 0, created_at: new Date(Date.now() - 7200000).toISOString(), updated_at: new Date(Date.now() - 7000000).toISOString() },
];

export default function ChecklistsPage() {
  const [checklists, setChecklists] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchChecklistRunList()
      .then(res => {
        if (res && res.data && Array.isArray(res.data)) {
          setChecklists(res.data);
        } else if (Array.isArray(res)) {
          setChecklists(res);
        } else {
          setChecklists(fallbackChecklists);
        }
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic fallback fixture", err);
        setChecklists(fallbackChecklists);
        setError("Backend API unavailable. Displaying deterministic fallback fixture.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const total = checklists.length;
  const inProgress = checklists.filter(c => c.status === 'IN_PROGRESS').length;
  const completed = checklists.filter(c => c.status === 'COMPLETED').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <CheckSquare className="w-8 h-8 text-[#00e5ff]" />
          Checklist Runs
        </h1>
        <p className="text-slate-400">
          Track active and completed equipment inspection plans.
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
              <span className="text-sm font-medium text-slate-400">Total Runs</span>
              <FileText className="w-4 h-4 text-slate-500" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : total}</div>
          </CardContent>
        </Card>
        <Card className="bg-[#00e5ff]/5 border-[#00e5ff]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#00e5ff]">In Progress</span>
              <Activity className="w-4 h-4 text-[#00e5ff]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : inProgress}</div>
          </CardContent>
        </Card>
        <Card className="bg-[#00cc66]/5 border-[#00cc66]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#00cc66]">Completed</span>
              <CheckCircle2 className="w-4 h-4 text-[#00cc66]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : completed}</div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card className="border-[#1a2c4d] overflow-hidden bg-[#0a1322]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-[#111d33] border-b border-[#1a2c4d] text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Checklist Run</th>
                <th className="px-4 py-3 font-medium">Equipment / Session</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Progress</th>
                <th className="px-4 py-3 font-medium">Last Updated</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a2c4d]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading checklists...</td>
                </tr>
              ) : checklists.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No checklists found.</td>
                </tr>
              ) : (
                checklists.map((chk) => (
                  <tr key={chk.id} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{chk.checklist_name}</div>
                      <div className="font-mono text-[#00e5ff] text-xs mt-0.5">{chk.id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-mono text-[#00e5ff] text-xs bg-[#00e5ff]/10 w-fit px-2 py-0.5 rounded border border-[#00e5ff]/20 mb-1">{chk.equipment_code}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{chk.diagnosis_session_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                        chk.status === 'IN_PROGRESS' ? 'bg-[#00e5ff]/10 text-[#00e5ff] border-[#00e5ff]/30' :
                        chk.status === 'COMPLETED' ? 'bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30' :
                        'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {chk.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-[#111d33] rounded-full h-1.5 flex-1 min-w-[60px] overflow-hidden">
                          <div className="bg-[#00cc66] h-1.5" style={{ width: `${(chk.completed_items / chk.total_items) * 100}%` }}></div>
                        </div>
                        <span className="text-xs text-slate-400">{chk.completed_items}/{chk.total_items}</span>
                      </div>
                      {chk.failed_items > 0 && <span className="text-[10px] text-[#ff3366] block mt-1">{chk.failed_items} BLOCKED</span>}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      <div className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(chk.updated_at).toLocaleDateString()}</div>
                      <div className="text-slate-600 ml-4">{new Date(chk.updated_at).toLocaleTimeString()}</div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/checklist-runs/${chk.id}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#111d33] hover:bg-[#1a2c4d] border border-[#1a2c4d] text-white rounded text-xs font-medium transition-colors">
                        Open Runner
                      </Link>
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
