"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSystemSafetySettings } from "@/lib/api";
import { Settings, ShieldCheck, Lock, AlertTriangle, Database, Info, Clock } from "lucide-react";

const fallbackSettings = {
  external_ai_enabled: false,
  equipment_control_enabled: false,
  interlock_bypass_allowed: false,
  output_forcing_allowed: false,
  human_approval_required: true,
  audit_logging_enabled: true,
  deterministic_engine_enabled: true,
  allowed_equipment_scope: ["LOAD_PORT", "FOUP_CLAMP", "ETHERCAT_IO"],
  policy_version: "v1.4.0",
  updated_at: new Date().toISOString()
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSystemSafetySettings()
      .then(res => {
        if (res && typeof res === 'object') {
          setSettings(res);
        } else {
          setSettings(fallbackSettings);
        }
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic fallback fixture", err);
        setSettings(fallbackSettings);
        setError("Backend API unavailable. Displaying deterministic fallback fixture.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Settings className="w-8 h-8 text-[#00e5ff]" />
          System Safety Settings
        </h1>
        <p className="text-slate-400">
          Review the operational boundaries and active policy configurations for FabMind Agent.
        </p>
      </div>

      <div className="bg-[#111d33] border border-[#1a2c4d] p-4 rounded-lg flex items-start gap-3">
        <Lock className="w-5 h-5 text-[#00e5ff] mt-0.5 shrink-0" />
        <div className="text-sm text-slate-300 leading-relaxed">
          <span className="font-bold text-white block mb-1">Safety Policy Enforced</span>
          The following security boundaries, equipment control limits, and operational scopes are strictly enforced by the backend configuration (`schema.sql` and API policy rules). They are completely read-only and cannot be altered from this web interface to prevent unauthorized risk escalation.
        </div>
      </div>

      {error && (
        <div className="bg-[#ffaa00]/10 border border-[#ffaa00]/30 text-[#ffaa00] p-3 rounded-md text-sm mt-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading safety settings...</div>
      ) : settings && (
        <div className="space-y-6 mt-6">
          
          <Card className="bg-[#050b14] border-[#1a2c4d]">
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#00cc66]" />
                Agentic Boundary Policy (v{settings.policy_version})
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
              
              <PolicyItem 
                label="External AI (LLM) Engine" 
                value={settings.external_ai_enabled} 
                danger={false}
                desc="Determines if external APIs are used for core logic."
              />
              <PolicyItem 
                label="Deterministic Engine" 
                value={settings.deterministic_engine_enabled} 
                danger={false}
                desc="Forces rule-based, predictable triage generation."
              />
              <PolicyItem 
                label="Equipment Control" 
                value={settings.equipment_control_enabled} 
                danger={true}
                desc="Write access to equipment PLCs or SECS/GEM."
              />
              <PolicyItem 
                label="Interlock Bypass" 
                value={settings.interlock_bypass_allowed} 
                danger={true}
                desc="Ability to bypass mechanical safety interlocks."
              />
              <PolicyItem 
                label="Output Forcing" 
                value={settings.output_forcing_allowed} 
                danger={true}
                desc="Ability to manually force EtherCAT I/O states."
              />
              <PolicyItem 
                label="Human Approval Required" 
                value={settings.human_approval_required} 
                danger={false}
                desc="Senior engineer must approve all diagnostic reports."
              />
              <PolicyItem 
                label="Immutable Audit Logging" 
                value={settings.audit_logging_enabled} 
                danger={false}
                desc="All actions logged securely to the audit ledger."
              />

            </CardContent>
          </Card>

          <Card className="bg-[#050b14] border-[#1a2c4d]">
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-[#00e5ff]" />
                Allowed Equipment Scope
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5">
              <div className="flex flex-wrap gap-2">
                {settings.allowed_equipment_scope && settings.allowed_equipment_scope.map((scope: string) => (
                  <span key={scope} className="px-3 py-1.5 bg-[#0a1322] border border-[#1a2c4d] text-slate-300 text-xs font-mono rounded">
                    {scope}
                  </span>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-4 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                The Agent will reject analysis requests for equipment outside this approved scope.
              </p>
            </CardContent>
          </Card>

          <div className="text-right text-xs text-slate-500 flex items-center justify-end gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Policy Generated: {new Date(settings.updated_at).toLocaleString()}
          </div>

        </div>
      )}

    </div>
  );
}

function PolicyItem({ label, value, danger, desc }: { label: string, value: boolean, danger: boolean, desc: string }) {
  return (
    <div className="p-3 bg-[#0a1322] border border-[#1a2c4d] rounded-lg">
      <div className="flex items-start justify-between mb-1.5">
        <span className="text-sm font-medium text-white">{label}</span>
        <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase border tracking-wider ${
          value 
            ? 'bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30' 
            : danger 
              ? 'bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30' // Safe states
              : 'bg-slate-800 text-slate-400 border-slate-700'
        }`}>
          {value ? 'ENABLED' : 'DISABLED'}
        </span>
      </div>
      <p className="text-xs text-slate-500">{desc}</p>
    </div>
  );
}
