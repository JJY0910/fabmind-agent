"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckSquare, ShieldAlert, Clock, Save, User, FileText, ChevronRight, AlertTriangle, AlertCircle, Database } from "lucide-react";
import Link from "next/link";
import { fetchChecklistRun, updateChecklistItem } from "@/lib/api";
import { WorkflowStepper } from "@/components/ui/WorkflowStepper";

const mockChecklistRun = {
  id: "RUN-LP-01",
  tenant_id: "TENANT-01",
  diagnosis_session_id: "LP-01-SESSION",
  agent_run_id: "RUN-001",
  created_by_user_id: "SYSTEM",
  status: "IN_PROGRESS",
  created_at: "2026-05-16T08:31:00Z",
  updated_at: "2026-05-16T08:45:00Z",
  items: [
    {
      id: "CHK-ITEM-1",
      tenant_id: "TENANT-01",
      checklist_run_id: "RUN-LP-01",
      source_inspection_plan_item_id: "I1",
      item_order: 1,
      title: "인터락 상태 확인",
      description: "HMI 또는 I/O 모니터에서 인터락 조건 충족 여부 확인",
      expected_result: "모든 인터락 조건 TRUE 확인",
      status: "DONE",
      field_note: "도어 닫힘 상태 및 FOUP 안착 센서 정상 동작 확인함.",
      completed_by_user_id: "Engineer Kim",
      completed_at: "2026-05-16T08:35:00Z"
    },
    {
      id: "CHK-ITEM-2",
      tenant_id: "TENANT-01",
      checklist_run_id: "RUN-LP-01",
      source_inspection_plan_item_id: "I2",
      item_order: 2,
      title: "센서 LED 확인",
      description: "Clamp 동작 시 센서 앰프의 동작 표시등 점등 확인",
      expected_result: "센서 감지 시 녹색 LED 점등",
      status: "IN_PROGRESS",
      field_note: "Clamp 솔레노이드 강제 on 후 확인 중. LED 점등 안됨.",
      completed_by_user_id: null,
      completed_at: null
    },
    {
      id: "CHK-ITEM-3",
      tenant_id: "TENANT-01",
      checklist_run_id: "RUN-LP-01",
      source_inspection_plan_item_id: "I3",
      item_order: 3,
      title: "센서 bracket 고정 상태 확인",
      description: "고정 볼트(M3) 조임 상태 확인",
      expected_result: "볼트 풀림 없이 단단히 고정되어 있을 것",
      status: "TODO",
      field_note: "",
      completed_by_user_id: null,
      completed_at: null
    }
  ]
};

const statusColors: Record<string, string> = {
  TODO: "bg-slate-800 text-slate-400 border-slate-700",
  IN_PROGRESS: "bg-[#00e5ff]/10 text-[#00e5ff] border-[#00e5ff]/30",
  DONE: "bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30",
  BLOCKED: "bg-[#ff3366]/10 text-[#ff3366] border-[#ff3366]/30",
  SKIPPED: "bg-slate-700/50 text-slate-500 border-slate-600"
};

export default function ChecklistRunnerPage() {
  const params = useParams();
  const runId = params?.checklistRunId as string;
  const [data, setData] = useState(mockChecklistRun);
  const [savingItem, setSavingItem] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    fetchChecklistRun(runId)
      .then(res => {
        if (res && res.id) setData(res);
      })
      .catch(err => {
        console.warn("Backend unavailable or schema mismatch, falling back to deterministic fixture", err);
      });
  }, [runId]);

  const handleUpdateItem = async (itemId: string, status: string, fieldNote: string) => {
    setSavingItem(itemId);
    try {
      const updatedRun = await updateChecklistItem(data.id, itemId, { status, field_note: fieldNote });
      if (updatedRun && updatedRun.id) {
        setData(updatedRun);
      } else {
        // Optimistic update if backend just returns ok or we are in mock mode
        updateLocal(itemId, status, fieldNote);
      }
    } catch (err) {
      console.warn("Update failed via API, updating local fixture state", err);
      updateLocal(itemId, status, fieldNote);
    } finally {
      setSavingItem(null);
    }
  };

  const updateLocal = (itemId: string, status: string, fieldNote: string) => {
    setData(prev => ({
      ...prev,
      items: prev.items.map(i => 
        i.id === itemId ? { ...i, status, field_note: fieldNote } : i
      )
    }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* Stepper */}
      <div className="mb-4">
        <WorkflowStepper currentStep="CHECKLIST" />
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Checklist Runner</h1>
            <span className={`px-2.5 py-0.5 rounded-full border text-xs font-bold uppercase tracking-wider ${
              data.status === 'COMPLETED' ? statusColors.DONE :
              data.status === 'IN_PROGRESS' ? statusColors.IN_PROGRESS :
              statusColors.TODO
            }`}>
              {data.status.replace('_', ' ')}
            </span>
          </div>
          <p className="text-slate-400">Agent-Recommended Inspection Plan Execution</p>
        </div>
        <div>
          <Link href={`/report-drafts/RPT-${data.diagnosis_session_id.replace('-SESSION', '')}`} className="px-4 py-2 bg-[#00e5ff] hover:bg-[#00e5ff]/90 text-[#050b14] rounded-md text-sm font-bold shadow-[0_0_15px_rgba(0,229,255,0.3)] transition-all whitespace-nowrap block">
            Continue to Report Draft
          </Link>
        </div>
      </div>

      <Card className="bg-[#050b14] border-[#1a2c4d]">
        <CardContent className="p-4 flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-slate-300">
              <Database className="w-4 h-4 text-[#00e5ff]" />
              <span className="font-mono">{data.diagnosis_session_id}</span>
            </div>
            <div className="w-px h-4 bg-[#1a2c4d]" />
            <div className="flex items-center gap-2 text-slate-300">
              <FileText className="w-4 h-4 text-slate-400" />
              <span className="font-mono text-slate-300">Run ID: <span className="text-[#00e5ff]">{data.id}</span></span>
            </div>
            <div className="w-px h-4 bg-[#1a2c4d]" />
            <div className="flex items-center gap-2 text-slate-300">
              <User className="w-4 h-4 text-slate-400" />
              <span>Assigned: {data.created_by_user_id}</span>
            </div>
          </div>
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" />
            Created {new Date(data.created_at).toLocaleString()}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {data.items.map((item) => (
          <ChecklistItemRow 
            key={item.id} 
            item={item} 
            isSaving={savingItem === item.id}
            onUpdate={(status, note) => handleUpdateItem(item.id, status, note)} 
          />
        ))}
      </div>
    </div>
  );
}

function ChecklistItemRow({ item, isSaving, onUpdate }: { item: any, isSaving: boolean, onUpdate: (status: string, note: string) => void }) {
  const [note, setNote] = useState(item.field_note || "");
  const [status, setStatus] = useState(item.status);

  // Sync if external data changes
  useEffect(() => {
    setNote(item.field_note || "");
    setStatus(item.status);
  }, [item]);

  const handleSave = () => {
    onUpdate(status, note);
  };

  return (
    <Card className={`border ${status === 'DONE' ? 'border-[#00cc66]/30 bg-[#050b14]' : status === 'IN_PROGRESS' ? 'border-[#00e5ff]/40 bg-[#00e5ff]/5' : status === 'BLOCKED' ? 'border-[#ff3366]/40 bg-[#ff3366]/5' : 'border-[#1a2c4d] bg-[#0a1322]'} transition-colors relative overflow-hidden`}>
      {status === 'IN_PROGRESS' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00e5ff]" />}
      {status === 'BLOCKED' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#ff3366]" />}
      {status === 'DONE' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00cc66]" />}

      <CardContent className="p-5 flex flex-col md:flex-row gap-6">
        {/* Left Info Column */}
        <div className="flex-1 space-y-3">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded bg-[#111d33] flex items-center justify-center text-xs font-mono text-slate-400 border border-[#1a2c4d] mt-0.5">
              {item.item_order}
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-white">{item.title}</h3>
              <p className="text-sm text-slate-300 mt-1">{item.description}</p>
            </div>
          </div>
          
          {item.expected_result && (
            <div className="ml-9 bg-[#111d33]/50 border border-[#1a2c4d] p-2.5 rounded text-sm text-slate-300 flex items-start gap-2">
              <CheckSquare className="w-4 h-4 text-[#00cc66] mt-0.5 flex-shrink-0" />
              <span><span className="text-slate-500 font-medium text-xs block mb-0.5">EXPECTED OBSERVATION</span>{item.expected_result}</span>
            </div>
          )}

          {status === 'BLOCKED' && (
            <div className="ml-9 bg-[#ff3366]/10 border border-[#ff3366]/30 p-2.5 rounded text-sm text-[#ff3366] flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span><span className="font-bold text-xs block mb-0.5">BLOCKED</span>Item cannot be completed due to missing permissions or safety policy.</span>
            </div>
          )}
        </div>

        {/* Right Input Column */}
        <div className="md:w-72 flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <select 
              value={status} 
              onChange={(e) => setStatus(e.target.value)}
              className={`flex-1 text-xs font-bold uppercase tracking-wider rounded border px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#00e5ff] appearance-none ${statusColors[status] || statusColors.TODO}`}
            >
              <option value="TODO">Todo</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="DONE">Done</option>
              <option value="BLOCKED">Blocked</option>
              <option value="SKIPPED">Skipped</option>
            </select>
          </div>

          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Field notes / observations..."
            className="w-full h-24 bg-[#050b14] border border-[#1a2c4d] rounded-md p-2.5 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:border-[#00e5ff] resize-none transition-colors"
          />

          <button 
            onClick={handleSave}
            disabled={isSaving || (status === item.status && note === (item.field_note || ""))}
            className="flex items-center justify-center gap-2 w-full py-2 bg-[#111d33] hover:bg-[#1a2c4d] disabled:opacity-50 disabled:hover:bg-[#111d33] border border-[#1a2c4d] rounded-md text-xs font-bold text-white transition-colors"
          >
            {isSaving ? <Clock className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isSaving ? "Saving..." : "Save Note"}
          </button>

          {item.completed_by_user_id && status === 'DONE' && (
            <div className="text-[10px] text-slate-500 text-right mt-1 flex flex-col">
              <span>Completed by {item.completed_by_user_id}</span>
              {item.completed_at && <span>{new Date(item.completed_at).toLocaleString()}</span>}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
