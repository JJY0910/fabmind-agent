"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ChecklistRunDetailDrawer, type ChecklistRunSummary } from "@/components/ui/checklist-run-detail-drawer";
import {
  CodePill,
  DataSourceBanner,
  OperationalTable,
  OperationalTableBody,
  OperationalTableHeader,
  StatusBadge,
  TableStateRow,
} from "@/components/ui/operational";
import { createReferenceListResponse, fetchChecklistRunList } from "@/lib/api";
import { CheckSquare, CheckCircle2, Clock, FileText, Activity } from "lucide-react";
import Link from "next/link";

const fallbackChecklists: ChecklistRunSummary[] = [
  { checklist_run_id: "RUN-LP-01", diagnosis_session_id: "LP-01-SESSION", equipment_code: "LP-01", checklist_name: "FOUP Clamp Sensor Misalignment Check", status: "IN_PROGRESS", total_items: 3, completed_items: 1, failed_items: 0, pending_items: 2, created_at: new Date(Date.now() - 3600000).toISOString(), updated_at: new Date(Date.now() - 1800000).toISOString() },
  { checklist_run_id: "RUN-FC-11", diagnosis_session_id: "FC-11-SESSION", equipment_code: "FC-11", checklist_name: "EtherCAT Slave Status Check", status: "COMPLETED", total_items: 5, completed_items: 5, failed_items: 0, pending_items: 0, created_at: new Date(Date.now() - 7200000).toISOString(), updated_at: new Date(Date.now() - 7000000).toISOString() },
];

type DataMode = "loading" | "live" | "reference" | "empty";

function formatTimestamp(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

export default function ChecklistsPage() {
  const [checklists, setChecklists] = useState<ChecklistRunSummary[]>([]);
  const [selectedChecklistRun, setSelectedChecklistRun] = useState<ChecklistRunSummary | null>(null);
  const [apiTotal, setApiTotal] = useState(0);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchChecklistRunList()
      .then(res => {
        setChecklists(res.items as ChecklistRunSummary[]);
        setApiTotal(res.total);
        setDataMode(res.items.length > 0 ? "live" : "empty");
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic reference data", err);
        const reference = createReferenceListResponse(fallbackChecklists);
        const message = err instanceof Error ? err.message : "Backend API unavailable";
        setChecklists(reference.items);
        setApiTotal(reference.total);
        setDataMode("reference");
        setError(`${message}. Showing deterministic reference data.`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const total = dataMode === "live" || dataMode === "empty" ? apiTotal : checklists.length;
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
        <DataSourceBanner
          mode="reference"
          message={error}
          detail="Operational API connection required for live checklist records."
        />
      )}

      {dataMode === "live" && (
        <DataSourceBanner mode="live" message={`Backend API connected. Showing ${apiTotal} checklist run${apiTotal === 1 ? "" : "s"}.`} />
      )}

      {dataMode === "empty" && (
        <DataSourceBanner mode="empty" message="Backend API connected. No checklist runs matched the current query." />
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

      <OperationalTable>
        <OperationalTableHeader>
          <tr>
            <th className="px-4 py-3 font-medium">Checklist Run</th>
            <th className="px-4 py-3 font-medium">Equipment / Session</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Progress</th>
            <th className="px-4 py-3 font-medium">Last Updated</th>
            <th className="px-4 py-3 font-medium text-right">Action</th>
          </tr>
        </OperationalTableHeader>
        <OperationalTableBody>
          {loading ? (
            <TableStateRow colSpan={6} title="Loading checklist runs..." detail="Reading checklist run records from the operational API." />
          ) : checklists.length === 0 ? (
            <TableStateRow colSpan={6} title="No checklist runs found." detail="No checklist run records are available in the current payload." />
          ) : (
            checklists.map((chk) => {
              const runId = chk.checklist_run_id ?? chk.id;
              const totalItems = Number(chk.total_items ?? 0);
              const completedItems = Number(chk.completed_items ?? 0);
              const failedItems = Number(chk.failed_items ?? 0);
              const progress = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
              return (
                <tr key={runId ?? `${chk.equipment_code ?? "unknown"}-${chk.diagnosis_session_id ?? "session"}`} className="transition-colors hover:bg-[#111d33]/50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-white">{chk.checklist_name ?? "Unnamed checklist run"}</div>
                    <div className="mt-1">
                      <CodePill>{runId ?? "UNKNOWN"}</CodePill>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <CodePill>{chk.equipment_code ?? "UNKNOWN"}</CodePill>
                    <div className="mt-1 font-mono text-[10px] text-slate-500">{chk.diagnosis_session_id ?? "No session in payload"}</div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={chk.status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 min-w-[64px] flex-1 overflow-hidden rounded-full bg-[#111d33]">
                        <div className="h-1.5 rounded-full bg-[#00cc66]" style={{ width: `${progress}%` }} />
                      </div>
                      <span className="text-xs text-slate-400">{completedItems}/{totalItems}</span>
                    </div>
                    {failedItems > 0 && <span className="mt-1 block text-[10px] text-[#ff3366]">{failedItems} blocked</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimestamp(chk.updated_at)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        className="inline-flex items-center rounded border border-[#00e5ff]/30 bg-[#00e5ff]/10 px-3 py-1.5 text-xs font-medium text-[#00e5ff] transition-colors hover:bg-[#00e5ff]/15 focus:outline-none focus:ring-2 focus:ring-[#00e5ff]/40"
                        onClick={() => setSelectedChecklistRun(chk)}
                      >
                        Inspect
                      </button>
                      {runId ? (
                        <Link href={`/checklist-runs/${runId}`} className="inline-flex items-center gap-1 rounded border border-[#1a2c4d] bg-[#111d33] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#1a2c4d]">
                          Open Runner
                        </Link>
                      ) : (
                        <span className="text-xs text-slate-600">Run ID unavailable</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </OperationalTableBody>
      </OperationalTable>

      <ChecklistRunDetailDrawer
        checklistRun={selectedChecklistRun}
        dataMode={dataMode}
        onClose={() => setSelectedChecklistRun(null)}
      />
    </div>
  );
}
