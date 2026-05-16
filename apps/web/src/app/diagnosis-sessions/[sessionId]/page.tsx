"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, ShieldAlert, FileText, CheckSquare, ShieldCheck, Microscope, Database, Clock, ChevronRight, CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";
import Link from "next/link";
import { fetchDiagnosisSession } from "@/lib/api";
import { WorkflowStepper } from "@/components/ui/WorkflowStepper";

// Deterministic fallback fixture matching contracts/openapi.yaml
const mockData = {
  session: {
    id: "LP-01-SESSION",
    equipment_id: "LP-01",
    alarm_code: "LP-CLAMP-014",
    symptom_summary: "FOUP clamp command 후 clamp done sensor가 들어오지 않음",
    ethercat_state: "OP",
    io_snapshot: { DO_CLAMP_SOL: true, DI_CLAMP_DONE: false },
    recent_action: "전일 clamp sensor bracket 조정",
    status: "ANALYSIS_READY",
    risk_level: "LOW",
    created_at: "2026-05-16T08:30:00Z"
  },
  agent_run: {
    run_id: "RUN-001",
    status: "COMPLETED",
    mode: "DETERMINISTIC",
    safety_result: "SAFE_READ_ONLY",
    risk_level: "LOW",
    steps: [
      { id: "S1", step_order: 1, name: "Input Normalization", status: "COMPLETED", summary: "Alarm LP-CLAMP-014 matched." },
      { id: "S2", step_order: 2, name: "I/O Interpretation", status: "COMPLETED", summary: "DO_CLAMP_SOL is true but DI_CLAMP_DONE is false." },
      { id: "S3", step_order: 3, name: "Evidence Retrieval", status: "COMPLETED", summary: "Found 2 related manuals and 1 maintenance log." },
      { id: "S4", step_order: 4, name: "Rule Scoring", status: "COMPLETED", summary: "Sensor misalignment ranked highest." },
      { id: "S5", step_order: 5, name: "Safety Guardrail", status: "COMPLETED", summary: "No risky actions detected." }
    ],
    hypotheses: [
      {
        id: "H1", rank: 1, title: "Clamp 완료 센서 위치 이탈 또는 감도 불량", 
        reasoning: "DO 명령은 정상 출력되었으나 DI 응답이 없고, 최근 bracket 조정 이력이 있어 물리적 정렬 문제가 유력함.", 
        confidence_band: "HIGH", risk_level: "LOW", evidence_ids: ["E1", "E2"]
      },
      {
        id: "H2", rank: 2, title: "Clamp 실린더 공압 라인 리크", 
        reasoning: "센서가 정상이더라도 실제 실린더가 전진하지 못했을 가능성.", 
        confidence_band: "LOW", risk_level: "MEDIUM", evidence_ids: []
      }
    ],
    evidence: [
      { id: "E1", source_type: "MANUAL", source_code: "DOC-LP-04", title: "LP-CLAMP-014 알람 대응 가이드", excerpt: "센서 브라켓 볼트 풀림 확인", relevance_reason: "알람 코드 직접 일치" },
      { id: "E2", source_type: "MAINT_LOG", source_code: "LOG-230911", title: "작업 이력: Sensor bracket 조정", excerpt: "센서 인식 불량으로 브라켓 위치 미세 조정함", relevance_reason: "최근 작업 이력과 증상 일치" }
    ],
    inspection_plan_items: [
      { id: "I1", item_order: 1, title: "인터락 상태 확인", instruction: "HMI 또는 I/O 모니터에서 인터락 조건 충족 여부 확인", safety_level: "NORMAL" },
      { id: "I2", item_order: 2, title: "센서 LED 확인", instruction: "Clamp 동작 시 센서 앰프의 동작 표시등 점등 확인", safety_level: "NORMAL" },
      { id: "I3", item_order: 3, title: "센서 bracket 고정 상태 확인", instruction: "고정 볼트(M3) 조임 상태 확인", safety_level: "CAUTION" }
    ]
  }
};

export default function DiagnosisSessionPage() {
  const params = useParams();
  const sessionId = params?.sessionId as string;
  const [data, setData] = useState(mockData);

  useEffect(() => {
    if (!sessionId) return;
    fetchDiagnosisSession(sessionId)
      .then(res => {
        // If backend returns the aggregate form, use it
        if (res && res.session && res.agent_run) {
          setData({ session: res.session, agent_run: res.agent_run });
        }
      })
      .catch((err) => {
        console.warn('Backend unavailable or schema mismatch, falling back to deterministic fixture', err);
      });
  }, [sessionId]);

  const { session, agent_run } = data;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* Top Navigation / Stepper */}
      <div className="mb-4">
        <WorkflowStepper currentStep="DIAGNOSIS" />
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Agent Analysis Results</h1>
            {agent_run.status === "COMPLETED" && (
              <span className="px-2.5 py-0.5 rounded-full bg-[#00cc66]/10 border border-[#00cc66]/30 text-[#00cc66] text-xs font-bold uppercase tracking-wider flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Analysis Complete
              </span>
            )}
          </div>
          <p className="text-slate-400">Deterministic Rule Engine Execution</p>
        </div>
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <Link href={`/checklist-runs/RUN-${session.id.replace('-SESSION', '')}`} className="px-4 py-2 bg-[#00e5ff] hover:bg-[#00e5ff]/90 text-[#050b14] rounded-md text-sm font-bold shadow-[0_0_15px_rgba(0,229,255,0.3)] transition-all whitespace-nowrap">
            Continue to Checklist Run
          </Link>
          <Link href={`/report-drafts/RPT-${session.id.replace('-SESSION', '')}`} className="px-4 py-2 bg-[#111d33] hover:bg-[#1a2c4d] border border-[#1a2c4d] text-[#00e5ff] rounded-md text-sm font-medium transition-colors whitespace-nowrap">
            Skip to Report Draft
          </Link>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Context & Timeline */}
        <div className="space-y-6 lg:col-span-1">
          
          {/* Situation Snapshot */}
          <Card>
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-[#00e5ff]" />
                Situation Snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Session ID</span>
                <span className="text-sm font-mono text-[#00e5ff] bg-[#00e5ff]/10 px-2 py-0.5 rounded">{session.id}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Equipment</span>
                <span className="text-sm font-mono text-white bg-[#1a2c4d] px-2 py-0.5 rounded">{session.equipment_id}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Alarm Code</span>
                <span className="text-sm font-mono text-[#ff3366] bg-[#ff3366]/10 px-2 py-0.5 rounded">{session.alarm_code}</span>
              </div>
              <div>
                <span className="text-xs text-slate-500 block mb-1">Symptom</span>
                <p className="text-sm text-slate-300 leading-relaxed bg-[#050b14] p-2 rounded border border-[#1a2c4d]">
                  {session.symptom_summary}
                </p>
              </div>
              <div className="pt-2 border-t border-[#1a2c4d]">
                <span className="text-xs text-slate-500 block mb-2">I/O State</span>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(session.io_snapshot).map(([key, val]) => (
                    <div key={key} className="flex flex-col bg-[#050b14] p-1.5 rounded border border-[#1a2c4d]">
                      <span className="text-[10px] text-slate-500 font-mono truncate">{key}</span>
                      <span className={`text-xs font-bold font-mono ${val ? 'text-[#00cc66]' : 'text-slate-500'}`}>
                        {val ? 'TRUE' : 'FALSE'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Agent Timeline */}
          <Card>
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#00e5ff]" />
                Agent Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-[#00e5ff]/50 before:to-transparent">
                {agent_run.steps.map((step, i) => (
                  <div key={step.id} className="relative flex items-start gap-3">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-[#111d33] border-2 border-[#00e5ff] flex items-center justify-center z-10 mt-0.5">
                      {step.status === "COMPLETED" && <div className="w-2 h-2 rounded-full bg-[#00e5ff]" />}
                    </div>
                    <div className="flex flex-col gap-1 pb-2">
                      <span className="text-sm font-medium text-slate-200">{step.name}</span>
                      <span className="text-xs text-slate-400">{step.summary}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

        </div>

        {/* Right Column: Hypotheses, Evidence, Plan */}
        <div className="space-y-6 lg:col-span-2">
          
          {/* Safety Guardrail */}
          {agent_run.safety_result === "SAFE_READ_ONLY" ? (
             <div className="bg-[#00cc66]/10 border border-[#00cc66]/30 rounded-lg p-3 flex items-start gap-3">
               <ShieldCheck className="w-5 h-5 text-[#00cc66] mt-0.5" />
               <div>
                 <h4 className="text-sm font-bold text-[#00cc66]">Safety Guardrail: Pass</h4>
                 <p className="text-xs text-[#00cc66]/80 mt-0.5">Analysis relies on read-only data. No risky actions requested.</p>
               </div>
             </div>
          ) : (
            <div className="bg-[#ff3366]/10 border border-[#ff3366]/30 rounded-lg p-3 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-[#ff3366] mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-[#ff3366]">Safety Guardrail: BLOCKED</h4>
                <p className="text-xs text-[#ff3366]/80 mt-0.5">Policy violation detected. Risky intervention prevented.</p>
              </div>
            </div>
          )}

          {/* Top Hypotheses */}
          <Card className="border-[#00e5ff]/30 shadow-[0_0_15px_rgba(0,229,255,0.05)] relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#00e5ff]/5 rounded-bl-full pointer-events-none" />
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Microscope className="w-4 h-4 text-[#00e5ff]" />
                Top Hypotheses
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              {agent_run.hypotheses.map((hyp) => (
                <div key={hyp.id} className={`p-4 rounded-lg border ${hyp.rank === 1 ? 'bg-[#00e5ff]/5 border-[#00e5ff]/30' : 'bg-[#050b14] border-[#1a2c4d]'}`}>
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex items-center gap-3">
                      <span className={`flex items-center justify-center w-6 h-6 rounded text-xs font-bold ${hyp.rank === 1 ? 'bg-[#00e5ff] text-[#050b14]' : 'bg-[#1a2c4d] text-slate-400'}`}>
                        #{hyp.rank}
                      </span>
                      <h4 className={`font-semibold ${hyp.rank === 1 ? 'text-[#00e5ff]' : 'text-slate-300'}`}>{hyp.title}</h4>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider ${hyp.confidence_band === 'HIGH' ? 'bg-[#00cc66]/20 text-[#00cc66] border border-[#00cc66]/30' : 'bg-slate-800 text-slate-400'}`}>
                      {hyp.confidence_band} CONFIDENCE
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed ml-9">
                    {hyp.reasoning}
                  </p>
                  
                  {/* Evidence Links */}
                  {hyp.evidence_ids.length > 0 && (
                    <div className="ml-9 mt-4 space-y-2">
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Linked Evidence</span>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {hyp.evidence_ids.map(eid => {
                          const ev = agent_run.evidence.find(e => e.id === eid);
                          if (!ev) return null;
                          return (
                            <div key={ev.id} className="bg-[#050b14] border border-[#1a2c4d] p-2.5 rounded flex flex-col gap-1.5 hover:border-[#00e5ff]/50 transition-colors cursor-default">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] bg-[#111d33] text-slate-400 px-1.5 py-0.5 rounded font-mono">{ev.source_code}</span>
                                <FileText className="w-3 h-3 text-[#00e5ff]" />
                              </div>
                              <span className="text-xs text-white truncate">{ev.title}</span>
                              <span className="text-[11px] text-slate-500 line-clamp-2 leading-snug">{ev.excerpt}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Inspection Plan */}
          <Card>
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#00e5ff]" />
                Recommended Inspection Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-3">
                {agent_run.inspection_plan_items.map((item) => (
                  <div key={item.id} className="flex gap-4 p-3 rounded-lg border border-[#1a2c4d] bg-[#050b14] hover:bg-[#111d33] transition-colors">
                    <div className="flex-shrink-0 w-6 h-6 rounded bg-[#1a2c4d] flex items-center justify-center text-xs font-mono text-slate-400 border border-[#1a2c4d]">
                      {item.item_order}
                    </div>
                    <div className="flex-1 flex flex-col gap-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white">{item.title}</span>
                        {item.safety_level === "CAUTION" && (
                          <span className="flex items-center gap-1 text-[10px] text-[#ffaa00] bg-[#ffaa00]/10 px-1.5 py-0.5 rounded border border-[#ffaa00]/20 uppercase">
                            <AlertTriangle className="w-3 h-3" /> Caution
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400 leading-relaxed">{item.instruction}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
}
