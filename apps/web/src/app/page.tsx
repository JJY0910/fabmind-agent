"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Clock, Activity, FileText, Microscope, ShieldAlert, Cpu, CheckSquare, PlayCircle } from "lucide-react";
import Link from "next/link";
import { fetchDashboardSummary } from "@/lib/api";
import { WorkflowStepper } from "@/components/ui/WorkflowStepper";

const mockSummary = {
  active_diagnosis_count: 7,
  pending_approval_count: 3,
  high_risk_count: 1,
  evidence_linked_rate: 98.5,
  open_checklist_count: 12,
  submitted_report_count: 4,
  approved_report_count: 156,
  recent_diagnosis_sessions: [
    { session_id: 'LP-01-SESSION', equipment_code: 'LP-01', alarm_code: 'LP-CLAMP-014', status: 'ANALYSIS_READY', risk_level: 'LOW', created_at: new Date(Date.now() - 600000).toISOString(), desc: 'Clamp 완료 센서 위치 이탈' },
    { session_id: 'LP-02-SESSION', equipment_code: 'LP-02', alarm_code: 'ECAT-STATE-021', status: 'ANALYZING', risk_level: 'HIGH', created_at: new Date(Date.now() - 3600000).toISOString(), desc: 'EtherCAT Slave PRE-OP 고착' },
    { session_id: 'FC-11-SESSION', equipment_code: 'FC-11', alarm_code: 'FC-INTERLOCK-03', status: 'CLOSED', risk_level: 'LOW', created_at: new Date(Date.now() - 10800000).toISOString(), desc: '도어 닫힘 상태 불량' }
  ],
  required_actions: [
    { action_type: 'APPROVAL_REQUIRED', resource_type: 'REPORT_DRAFT', resource_id: 'RPT-092', title: 'EtherCAT state anomaly requires senior review (Engineer Kim)', severity: 'HIGH' }
  ],
  guardrail_blocks_today: 3
};

export default function HomePage() {
  const [summary, setSummary] = useState(mockSummary);

  useEffect(() => {
    fetchDashboardSummary()
      .then(data => {
        if (data && data.active_diagnosis_count !== undefined) {
          setSummary(data);
        }
      })
      .catch((err) => {
        console.warn('Backend unavailable, falling back to deterministic fixture', err);
      });
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">

      {/* Page Header */}
      <div className="flex flex-col gap-4 mb-8">
        <WorkflowStepper currentStep="DASHBOARD" />
        <div className="flex flex-col gap-2 mt-4">
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Cpu className="w-8 h-8 text-[#00e5ff]" />
            Operations Center
          </h1>
          <p className="text-slate-400">
            Load Port & FOUP Clamp Evidence-First AI Diagnostics
          </p>
        </div>
      </div>

      {/* Golden Path Entry */}
      <Card className="border-[#00e5ff]/30 bg-[linear-gradient(110deg,#0a1322_0%,#111d33_100%)] shadow-[0_0_20px_rgba(0,229,255,0.05)]">
        <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <PlayCircle className="w-6 h-6 text-[#00e5ff]" />
              Operational Workflow: Load Port FOUP Clamp Alarm
            </h2>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Follow one complete evidence-based troubleshooting workflow from alarm triage to senior approval and audit review.
            </p>
            <div className="flex gap-3 pt-2">
              <span className="text-xs font-mono bg-[#050b14] border border-[#1a2c4d] text-[#00e5ff] px-2 py-1 rounded">Load Port LP-01</span>
              <span className="text-xs font-mono bg-[#050b14] border border-[#1a2c4d] text-slate-300 px-2 py-1 rounded">FOUP Clamp / EtherCAT I/O</span>
            </div>
          </div>
          <Link
            href="/diagnosis-sessions/LP-01-SESSION"
            className="shrink-0 px-6 py-3 bg-[#00e5ff] hover:bg-[#00e5ff]/90 text-[#050b14] rounded-md text-sm font-bold shadow-[0_0_15px_rgba(0,229,255,0.3)] transition-all whitespace-nowrap"
          >
            Start Golden Path
          </Link>
        </CardContent>
      </Card>

      {/* System Status Panel (Metrics) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-[#00e5ff]/30 bg-[#00e5ff]/5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[#00e5ff]/10 rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform" />
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-[#00e5ff]">Active Diagnosis</p>
              <Activity className="h-4 w-4 text-[#00e5ff]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{summary.active_diagnosis_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Pending Approval</p>
              <Clock className="h-4 w-4 text-[#ffaa00]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{summary.pending_approval_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">High Risk Active</p>
              <ShieldAlert className="h-4 w-4 text-[#ff3366]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{summary.high_risk_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 relative overflow-hidden">
             <div className="absolute top-0 right-0 w-24 h-24 bg-[#00cc66]/5 rounded-bl-full pointer-events-none" />
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Evidence Linked</p>
              <FileText className="h-4 w-4 text-[#00cc66]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{summary.evidence_linked_rate}%</div>
          </CardContent>
        </Card>

        {/* Second Row of Metrics */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Open Checklists</p>
              <CheckSquare className="h-4 w-4 text-slate-500" />
            </div>
            <div className="text-2xl font-bold text-white mt-2">{summary.open_checklist_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Submitted Reports</p>
              <FileText className="h-4 w-4 text-[#ffaa00]" />
            </div>
            <div className="text-2xl font-bold text-white mt-2">{summary.submitted_report_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Approved Reports</p>
              <CheckCircle2 className="h-4 w-4 text-[#00cc66]" />
            </div>
            <div className="text-2xl font-bold text-white mt-2">{summary.approved_report_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Guardrail Blocks (Today)</p>
              <AlertCircle className="h-4 w-4 text-[#ff3366]" />
            </div>
            <div className="text-2xl font-bold text-white mt-2">{summary.guardrail_blocks_today}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 pt-4">

        {/* Golden Path Section */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Microscope className="w-5 h-5 text-slate-400" />
              Recent Diagnostic Sessions
            </h2>
            <button className="text-xs text-[#00e5ff] hover:text-white transition-colors border border-[#00e5ff]/30 px-3 py-1.5 rounded-md hover:bg-[#00e5ff]/10">
              View All
            </button>
          </div>

          <Card className="border-[#1a2c4d] overflow-hidden">
            <div className="divide-y divide-[#1a2c4d]">
              {summary.recent_diagnosis_sessions.map((item, i) => {
                const isGoldenPath = item.equipment_code === 'LP-01';
                const statusColor = item.status === 'CLOSED' ? 'text-slate-500' : 'text-[#00cc66]';

                const content = (
                  <div className="p-4 hover:bg-[#111d33] transition-colors flex items-center justify-between group cursor-pointer">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-white text-xs bg-[#1a2c4d] px-2 py-0.5 rounded border border-[#1a2c4d] group-hover:border-[#00e5ff]/30 transition-colors">{item.equipment_code}</span>
                        <span className="font-mono text-[#00e5ff] text-sm font-medium">{item.alarm_code}</span>
                      </div>
                      <span className="text-sm text-slate-300">{item.desc}</span>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className={`text-sm font-medium ${statusColor}`}>
                        {item.status.replace('_', ' ')}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] uppercase tracking-wider font-bold border px-2 py-0.5 rounded-full ${
                          item.risk_level === 'HIGH' ? 'border-[#ff3366]/30 text-[#ff3366] bg-[#ff3366]/10' :
                          'border-slate-700 text-slate-400 bg-slate-800/50'
                        }`}>
                          {item.risk_level} Risk
                        </span>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(item.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                    </div>
                  </div>
                );

                if (isGoldenPath) {
                  return (
                    <Link key={i} href={`/diagnosis-sessions/${item.session_id}`} className="block outline-none focus:ring-2 focus:ring-[#00e5ff] rounded-t-lg">
                      {content}
                    </Link>
                  );
                }

                return (
                  <div key={i}>
                    {content}
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Pending Approvals & Risk Summary */}
        <div className="space-y-6">

          {/* Approvals */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-slate-400" />
              Required Actions
            </h2>

            {summary.required_actions.map((action, i) => (
              <Card key={i} className="border-[#ffaa00]/30 bg-[#ffaa00]/5 shadow-[0_0_15px_rgba(255,170,0,0.05)]">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-[#ffaa00] flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4" />
                    Pending Approval (1)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-[#0a1322] border border-[#1a2c4d] p-3.5 rounded-lg">
                    <div className="flex items-center justify-between mb-2 border-b border-[#1a2c4d] pb-2">
                      <span className="font-mono text-xs text-[#00e5ff] bg-[#00e5ff]/10 px-2 py-0.5 rounded">{action.resource_id}</span>
                      <span className="text-[10px] font-mono bg-[#1a2c4d] px-2 py-0.5 rounded text-slate-300">TYPE: {action.action_type}</span>
                    </div>
                    <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                      {action.title}
                    </p>
                    <div className="flex gap-2">
                      <button className="flex-1 bg-[#ffaa00] hover:bg-[#ffaa00]/90 text-black text-xs font-bold py-2 rounded transition-colors shadow-sm">
                        Review Request
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Guardrails Dashboard Component remains as visual anchor */}
          <div className="space-y-4">
            <Card className="bg-[#050b14]">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-slate-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-[#ff3366]" />
                  Recent Guardrail Blocks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex flex-col gap-1.5 pb-3 border-b border-[#1a2c4d]">
                    <span className="text-xs font-mono text-[#ff3366] bg-[#ff3366]/10 w-fit px-1.5 py-0.5 rounded">POLICY_BLOCKED_RISKY_ACTION</span>
                    <span className="text-xs text-slate-300 leading-relaxed border-l-2 border-[#1a2c4d] pl-2 my-1">
                      "인터락 무시하고 강제로 clamp 동작시키면 되지 않나요?"
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">Agent Response: Action Denied.</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pt-1">
                    <span className="text-slate-400">See full log in Audit Console</span>
                    <Link href="/audit-events" className="text-[#00e5ff] hover:underline">View Audit Log</Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

        </div>
      </div>
    </div>
  );
}
