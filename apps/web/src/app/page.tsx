import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Clock, Activity, FileText, Microscope, ShieldAlert, Cpu } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Page Header */}
      <div className="flex flex-col gap-2 mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Cpu className="w-8 h-8 text-[#00e5ff]" />
          Operations Center
        </h1>
        <p className="text-slate-400">
          Load Port & FOUP Clamp Evidence-First AI Diagnostics
        </p>
      </div>

      {/* System Status Panel (Metrics) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-[#00e5ff]/30 bg-[#00e5ff]/5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[#00e5ff]/10 rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform" />
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-[#00e5ff]">Active Diagnosis</p>
              <Activity className="h-4 w-4 text-[#00e5ff]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">7</div>
            <p className="text-xs text-slate-400 mt-1">2 critical priority</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Pending Approval</p>
              <Clock className="h-4 w-4 text-[#ffaa00]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">3</div>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#ffaa00] inline-block animate-pulse"></span>
              Requires Senior Sign-off
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">High Risk Actions</p>
              <ShieldAlert className="h-4 w-4 text-[#ff3366]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">1</div>
            <p className="text-xs text-[#ff3366]/80 mt-1">Policy blocked intervention</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 relative overflow-hidden">
             <div className="absolute top-0 right-0 w-24 h-24 bg-[#00cc66]/5 rounded-bl-full pointer-events-none" />
            <div className="flex items-center justify-between space-y-0 pb-2">
              <p className="text-sm font-medium text-slate-400">Evidence Linked</p>
              <FileText className="h-4 w-4 text-[#00cc66]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">98%</div>
            <p className="text-xs text-slate-400 mt-1">Traceability maintained</p>
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
              {[
                { eq: 'LP-01', alarm: 'LP-CLAMP-014', time: '10 mins ago', status: 'Analysis Complete', risk: 'Low', color: 'text-[#00cc66]', desc: 'Clamp 완료 센서 위치 이탈' },
                { eq: 'LP-02', alarm: 'ECAT-STATE-021', time: '1 hour ago', status: 'Pending Approval', risk: 'High', color: 'text-[#ffaa00]', desc: 'EtherCAT Slave PRE-OP 고착' },
                { eq: 'FC-11', alarm: 'FC-INTERLOCK-03', time: '3 hours ago', status: 'Resolved', risk: 'Low', color: 'text-slate-500', desc: '도어 닫힘 상태 불량' },
              ].map((item, i) => {
                const content = (
                  <div className="p-4 hover:bg-[#111d33] transition-colors flex items-center justify-between group">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-white text-xs bg-[#1a2c4d] px-2 py-0.5 rounded border border-[#1a2c4d] group-hover:border-[#00e5ff]/30 transition-colors">{item.eq}</span>
                        <span className="font-mono text-[#00e5ff] text-sm font-medium">{item.alarm}</span>
                      </div>
                      <span className="text-sm text-slate-300">{item.desc}</span>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className={`text-sm font-medium ${item.color}`}>
                        {item.status}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] uppercase tracking-wider font-bold border px-2 py-0.5 rounded-full ${
                          item.risk === 'High' ? 'border-[#ff3366]/30 text-[#ff3366] bg-[#ff3366]/10' : 
                          'border-slate-700 text-slate-400 bg-slate-800/50'
                        }`}>
                          {item.risk} Risk
                        </span>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {item.time}
                        </span>
                      </div>
                    </div>
                  </div>
                );

                if (item.eq === 'LP-01') {
                  return (
                    <Link key={i} href="/diagnosis-sessions/LP-01-SESSION" className="block outline-none focus:ring-2 focus:ring-[#00e5ff] rounded-t-lg">
                      {content}
                    </Link>
                  );
                }

                return (
                  <div key={i} className="cursor-pointer">
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
            
            <Card className="border-[#ffaa00]/30 bg-[#ffaa00]/5 shadow-[0_0_15px_rgba(255,170,0,0.05)]">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-[#ffaa00] flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4" />
                  Pending Approvals (1)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-[#0a1322] border border-[#1a2c4d] p-3.5 rounded-lg">
                  <div className="flex items-center justify-between mb-2 border-b border-[#1a2c4d] pb-2">
                    <span className="font-mono text-xs text-[#00e5ff] bg-[#00e5ff]/10 px-2 py-0.5 rounded">LP-02</span>
                    <span className="text-[10px] font-mono bg-[#1a2c4d] px-2 py-0.5 rounded text-slate-300">ACTION: SERVO_RESET</span>
                  </div>
                  <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                    EtherCAT OP 강제 전환을 위한 Servo Reset 권한 요청 (Engineer Kim)
                  </p>
                  <div className="flex gap-2">
                    <button className="flex-1 bg-[#ffaa00] hover:bg-[#ffaa00]/90 text-black text-xs font-bold py-2 rounded transition-colors shadow-sm">
                      Review Request
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Guardrails */}
          <div className="space-y-4">
            <Card className="bg-[#050b14]">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-slate-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-[#ff3366]" />
                  Guardrail Blocks (Today)
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
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                    <span>Total prevented:</span>
                    <span className="text-white font-medium bg-[#1a2c4d] px-2 py-0.5 rounded">3 instances</span>
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
