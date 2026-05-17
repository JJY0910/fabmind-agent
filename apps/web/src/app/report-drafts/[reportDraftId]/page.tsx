"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { approveReportDraft, fetchCurrentUser, fetchReportDraft, rejectReportDraft, submitReportDraft, type AuthUser } from "@/lib/api";
import {
  FileText, ShieldCheck, Microscope, Database, AlertCircle, Clock,
  CheckCircle2, AlertTriangle, ShieldAlert, CheckSquare, User, History
} from "lucide-react";
import Link from "next/link";
import { WorkflowStepper } from "@/components/ui/WorkflowStepper";

const referenceReportDraft = {
  id: "RPT-LP-01",
  tenant_id: "TENANT-01",
  diagnosis_session_id: "LP-01-SESSION",
  agent_run_id: "RUN-001",
  checklist_run_id: "RUN-LP-01",
  created_by_user_id: "Engineer Kim",
  title: "FOUP Clamp Sensor State Mismatch Investigation",
  summary: "Clamp done sensor (DI_CLAMP_DONE) is failing to register despite the observed DO_CLAMP_SOL output state due to physical bracket loosening. Diagnosed and verified via deterministic rule matching and physical inspection.",
  root_cause: "M3 mounting bolts for the clamp verification sensor bracket loosened over repeated FOUP loading cycles, shifting the sensor 3mm out of optical range.",
  evidence_summary: "Agent matched alarm LP-CLAMP-014 against DOC-LP-04 manual. I/O snapshot confirmed DO_CLAMP_SOL=TRUE but DI_CLAMP_DONE=FALSE.",
  inspection_summary: "Physical inspection (Checklist RUN-LP-01) confirmed sensor LED does not illuminate on clamp actuation. Bracket was found to be loose to the touch.",
  recommended_action: "1. Stop at read-only diagnosis and do not initiate state-changing equipment actions from this system.\n2. Verify FOUP clamp sensor state, bracket seating, and EtherCAT I/O mapping against site-approved checklist.\n3. Record inspection findings and attach evidence before requesting senior review.\n4. Escalate to a senior engineer for any mechanical adjustment or maintenance action.",
  safety_notes: "This report is for evidence-based troubleshooting support only. Follow site safety procedures before any physical inspection, and always inspect according to site-approved procedure. Senior approval is required before maintenance action.",
  status: "DRAFT",
  created_at: "2026-05-16T09:00:00Z",
  updated_at: "2026-05-16T09:15:00Z",
  approvals: [] as any[]
};

const statusColors: Record<string, { bg: string, border: string, text: string }> = {
  DRAFT: { bg: "bg-slate-800/50", border: "border-slate-700", text: "text-slate-300" },
  SUBMITTED: { bg: "bg-[#ffaa00]/10", border: "border-[#ffaa00]/30", text: "text-[#ffaa00]" },
  APPROVED: { bg: "bg-[#00cc66]/10", border: "border-[#00cc66]/30", text: "text-[#00cc66]" },
  REJECTED: { bg: "bg-[#ff3366]/10", border: "border-[#ff3366]/30", text: "text-[#ff3366]" }
};

type DataMode = "loading" | "live" | "reference";

function formatTimestamp(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

function hasApprovalAuthority(user: AuthUser | null) {
  return user?.role === "SENIOR_ENGINEER" || user?.role === "ADMIN";
}

export default function ReportDraftPage() {
  const params = useParams();
  const rawId = params?.reportDraftId as string;
  const draftId = rawId || referenceReportDraft.id;

  const [data, setData] = useState(referenceReportDraft);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);

  useEffect(() => {
    fetchCurrentUser()
      .then(user => {
        setCurrentUser(user);
        setPermissionError(null);
      })
      .catch(err => {
        console.warn("Approval permissions unavailable", err);
        setCurrentUser(null);
        setPermissionError("Approval permissions unavailable. Senior/admin role required for final report decisions.");
      });
  }, []);

  useEffect(() => {
    if (!draftId) return;
    setDataMode("loading");
    fetchReportDraft(draftId)
      .then(res => {
        if (!res || !res.id) {
          throw new Error("Malformed report draft response from API");
        }
        setData(res);
        setDataMode("live");
        setActionError(null);
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic reference report", err);
        setData(referenceReportDraft);
        setDataMode("reference");
      });
  }, [draftId]);

  const handleAction = async (actionType: 'SUBMIT' | 'APPROVE' | 'REJECT') => {
    setActionError(null);
    if (dataMode !== "live") {
      setActionError("Backend API connection required before report workflow actions can be submitted.");
      return;
    }
    if (!currentUser) {
      setActionError("Current user authorization unavailable. Sign in with an operational account before changing report state.");
      return;
    }
    if ((actionType === "APPROVE" || actionType === "REJECT") && !hasApprovalAuthority(currentUser)) {
      setActionError("Senior/admin role required for final report decisions.");
      return;
    }

    setLoadingAction(actionType);
    try {
      let res;
      if (actionType === 'SUBMIT') res = await submitReportDraft(data.id);
      else if (actionType === 'APPROVE') res = await approveReportDraft(data.id, { comment: "Approved." });
      else if (actionType === 'REJECT') res = await rejectReportDraft(data.id, { comment: rejectReason });

      if (res && res.id) {
        setData(res);
        setDataMode("live");
      }
    } catch (err) {
      console.warn(`Failed to ${actionType} via API`, err);
      const message = err instanceof Error ? err.message : "Report workflow action failed";
      setActionError(message);
    } finally {
      setLoadingAction(null);
      setShowRejectInput(false);
      setRejectReason("");
    }
  };

  const statusStyle = statusColors[data.status] || statusColors.DRAFT;
  const canSubmit = dataMode === "live" && currentUser !== null;
  const canDecide = dataMode === "live" && hasApprovalAuthority(currentUser);

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">

      <div className="flex items-center justify-end mb-4 border-b border-[#1a2c4d] pb-2">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <User className="w-3.5 h-3.5" />
          {currentUser ? (
            <span>
              Signed in as <span className="text-slate-300">{currentUser.display_name ?? currentUser.username}</span>
              <span className="font-mono text-[#00e5ff]"> ({currentUser.role})</span>
            </span>
          ) : (
            <span>Approval permissions unavailable</span>
          )}
        </div>
      </div>

      {/* Stepper */}
      <div className="mb-4">
        <WorkflowStepper currentStep="REPORT" />
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">{data.title}</h1>
            <span className={`px-2.5 py-0.5 rounded-full border text-xs font-bold uppercase tracking-wider ${statusStyle.bg} ${statusStyle.border} ${statusStyle.text}`}>
              {data.status}
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <div className="flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-[#00e5ff]" />
              <span className="font-mono">{data.id}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Database className="w-4 h-4 text-[#00e5ff]" />
              <span className="font-mono">LP-01 (Load Port / FOUP Clamp)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-[#ff3366]" />
              <span className="font-mono">LP-CLAMP-014</span>
            </div>
            <div className="flex items-center gap-1.5">
              <User className="w-4 h-4" />
              <span>Created by {data.created_by_user_id}</span>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-3">
          <div className="text-right text-xs text-slate-500 flex flex-col gap-1">
            <span className="flex items-center justify-end gap-1"><Clock className="w-3.5 h-3.5" /> Created: {formatTimestamp(data.created_at)}</span>
            <span>Updated: {formatTimestamp(data.updated_at)}</span>
          </div>
          {(data.status === "APPROVED" || data.status === "REJECTED") && (
            <Link href="/audit-events" className="flex items-center gap-2 px-4 py-2 bg-[#111d33] hover:bg-[#1a2c4d] border border-[#1a2c4d] text-slate-300 rounded-md text-sm font-medium transition-colors">
              <History className="w-4 h-4 text-[#00e5ff]" />
              View in Audit Console
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">

        {/* Left Column (Metadata & Context) */}
        <div className="space-y-6 lg:col-span-1">
          <Card>
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-[#00e5ff]" />
                Diagnosis Context
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Session ID</span>
                <Link href={`/diagnosis-sessions/${data.diagnosis_session_id}`} className="text-sm font-mono text-[#00e5ff] hover:underline">
                  {data.diagnosis_session_id}
                </Link>
              </div>
              <div>
                <span className="text-xs text-slate-500 block mb-1">Problem Summary</span>
                <p className="text-sm text-slate-300 leading-relaxed bg-[#050b14] p-2.5 rounded border border-[#1a2c4d]">
                  Clamp done sensor (DI_CLAMP_DONE) is failing to register despite the observed DO_CLAMP_SOL output state.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Microscope className="w-4 h-4 text-[#00e5ff]" />
                Agent Analysis Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div className="flex items-start gap-2 text-sm text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-[#00cc66] mt-0.5 shrink-0" />
                <p>Deterministic rule engine matched alarm to manual DOC-LP-04.</p>
              </div>
              <div className="flex items-start gap-2 text-sm text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-[#00cc66] mt-0.5 shrink-0" />
                <p>Identified high probability of physical sensor misalignment.</p>
              </div>
              <div className="bg-[#00e5ff]/5 border border-[#00e5ff]/20 p-2.5 rounded mt-2">
                <span className="text-xs font-semibold text-[#00e5ff] uppercase tracking-wider block mb-1">Confidence</span>
                <span className="text-sm text-white font-mono">HIGH (Deterministic Evidence)</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#00e5ff]" />
                Checklist Results
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Checklist Run ID</span>
                <Link href={`/checklist-runs/${data.checklist_run_id}`} className="text-sm font-mono text-[#00e5ff] hover:underline">
                  {data.checklist_run_id}
                </Link>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-[#050b14] border border-[#1a2c4d] p-2 text-center rounded flex flex-col">
                  <span className="text-xl font-bold text-[#00cc66]">3</span>
                  <span className="text-[10px] text-slate-500 font-bold">DONE</span>
                </div>
                <div className="bg-[#050b14] border border-[#1a2c4d] p-2 text-center rounded flex flex-col">
                  <span className="text-xl font-bold text-slate-400">0</span>
                  <span className="text-[10px] text-slate-500 font-bold">PENDING</span>
                </div>
                <div className="bg-[#050b14] border border-[#1a2c4d] p-2 text-center rounded flex flex-col">
                  <span className="text-xl font-bold text-[#ff3366]">0</span>
                  <span className="text-[10px] text-slate-500 font-bold">FAILED</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (Report Content & Workflow) */}
        <div className="space-y-6 lg:col-span-2">

          <Card className="border-[#00e5ff]/20 shadow-[0_0_20px_rgba(0,229,255,0.03)]">
            <CardHeader className="bg-[#0a1322] border-b border-[#1a2c4d]">
              <CardTitle className="text-lg text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#00e5ff]" />
                Final Diagnostic Report
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 divide-y divide-[#1a2c4d]">

              <div className="p-5 hover:bg-[#111d33]/50 transition-colors">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Executive Summary</h3>
                <p className="text-sm text-slate-200 leading-relaxed">{data.summary}</p>
              </div>

              <div className="p-5 hover:bg-[#111d33]/50 transition-colors">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 text-[#00e5ff]">Root Cause</h3>
                <p className="text-sm text-white font-medium leading-relaxed">{data.root_cause}</p>
              </div>

              <div className="p-5 hover:bg-[#111d33]/50 transition-colors">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Evidence Summary</h3>
                <p className="text-sm text-slate-300 leading-relaxed bg-[#050b14] border border-[#1a2c4d] p-3 rounded font-mono text-[13px]">
                  {data.evidence_summary}
                </p>
              </div>

              <div className="p-5 hover:bg-[#111d33]/50 transition-colors">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Inspection Summary</h3>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {data.inspection_summary}
                </p>
              </div>

              <div className="p-5 hover:bg-[#111d33]/50 transition-colors">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 text-[#00cc66]">Recommended Action</h3>
                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {data.recommended_action}
                </div>
              </div>

              <div className="p-5 bg-[#ff3366]/5">
                <h3 className="text-xs font-bold text-[#ff3366] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" />
                  Safety Notes
                </h3>
                <p className="text-sm text-[#ff3366]/90 leading-relaxed font-medium">
                  {data.safety_notes}
                </p>
              </div>

            </CardContent>
          </Card>

          {/* Approval Workflow Block */}
          <Card className="border-[#1a2c4d] bg-[#050b14]">
            <CardHeader className="pb-3 border-b border-[#1a2c4d]">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#00e5ff]" />
                Approval Workflow
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5">
              {dataMode === "reference" && (
                <div className="bg-[#ffaa00]/10 border border-[#ffaa00]/30 p-3 rounded-lg mb-4 text-sm text-[#ffaa00]">
                  Backend API unavailable. Showing deterministic reference data. Report workflow actions are disabled until live API data is available.
                </div>
              )}

              {permissionError && (
                <div className="bg-[#111d33] border border-[#1a2c4d] p-3 rounded-lg mb-4 text-sm text-slate-300">
                  {permissionError}
                </div>
              )}

              {actionError && (
                <div className="bg-[#ff3366]/10 border border-[#ff3366]/30 p-3 rounded-lg mb-4 text-sm text-[#ff3366]">
                  {actionError}
                </div>
              )}

              {data.status === "DRAFT" && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <p className="text-sm text-slate-400">Report is currently a draft. Submit it to Senior Engineers for approval.</p>
                  <button
                    onClick={() => handleAction('SUBMIT')}
                    disabled={!canSubmit || loadingAction === 'SUBMIT'}
                    className="px-6 py-2 bg-[#ffaa00] hover:bg-[#ffaa00]/90 text-black rounded-md text-sm font-bold shadow-[0_0_15px_rgba(255,170,0,0.3)] transition-all whitespace-nowrap disabled:opacity-50"
                  >
                    {loadingAction === 'SUBMIT' ? "Submitting..." : "Submit for Approval"}
                  </button>
                </div>
              )}

              {data.status === "SUBMITTED" && (
                <div className="space-y-4">
                  <div className="bg-[#ffaa00]/10 border border-[#ffaa00]/30 p-3 rounded-lg flex items-start gap-3">
                    <Clock className="w-5 h-5 text-[#ffaa00] mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="text-sm font-bold text-[#ffaa00]">Pending Senior Approval</h4>
                      <p className="text-xs text-[#ffaa00]/80 mt-1">This report has been submitted and is awaiting review.</p>
                    </div>
                  </div>

                  {!canDecide ? (
                    <div className="bg-[#111d33] border border-[#1a2c4d] p-3 rounded text-sm text-slate-400 text-center">
                      <AlertCircle className="w-4 h-4 inline-block mr-1.5 mb-0.5" />
                      Senior/admin role required. Backend authorization remains the enforcement source of truth.
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      {showRejectInput ? (
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder="Reason for rejection..."
                            className="flex-1 bg-[#0a1322] border border-[#ff3366]/50 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-[#ff3366]"
                            autoFocus
                          />
                          <button
                            onClick={() => handleAction('REJECT')}
                            disabled={!rejectReason.trim() || loadingAction === 'REJECT'}
                            className="px-4 py-2 bg-[#ff3366] hover:bg-[#ff3366]/90 text-white rounded text-sm font-bold disabled:opacity-50"
                          >
                            Confirm Reject
                          </button>
                          <button
                            onClick={() => setShowRejectInput(false)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded text-sm font-medium"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-3">
                          <button
                            onClick={() => setShowRejectInput(true)}
                            className="px-6 py-2 bg-transparent border border-[#ff3366] hover:bg-[#ff3366]/10 text-[#ff3366] rounded-md text-sm font-bold transition-all"
                          >
                            Reject
                          </button>
                          <button
                            onClick={() => handleAction('APPROVE')}
                            disabled={loadingAction === 'APPROVE'}
                            className="px-6 py-2 bg-[#00cc66] hover:bg-[#00cc66]/90 text-[#050b14] rounded-md text-sm font-bold shadow-[0_0_15px_rgba(0,204,102,0.3)] transition-all disabled:opacity-50"
                          >
                            {loadingAction === 'APPROVE' ? "Approving..." : "Approve Report"}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {(data.status === "APPROVED" || data.status === "REJECTED") && data.approvals && data.approvals.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Review History</h4>
                  {data.approvals.map((app, idx) => (
                    <div key={idx} className={`p-3 rounded border flex items-start gap-3 ${app.decision === 'APPROVED' ? 'bg-[#00cc66]/5 border-[#00cc66]/20' : 'bg-[#ff3366]/5 border-[#ff3366]/20'}`}>
                      {app.decision === 'APPROVED' ? <CheckCircle2 className="w-5 h-5 text-[#00cc66] mt-0.5" /> : <ShieldAlert className="w-5 h-5 text-[#ff3366] mt-0.5" />}
                      <div className="flex-1">
                        <div className="flex justify-between items-start">
                          <span className={`text-sm font-bold ${app.decision === 'APPROVED' ? 'text-[#00cc66]' : 'text-[#ff3366]'}`}>
                            {app.decision} by {app.approver_user_id}
                          </span>
                          <span className="text-[10px] text-slate-500">{new Date(app.decided_at).toLocaleString()}</span>
                        </div>
                        {app.comment && (
                          <p className="text-sm text-slate-300 mt-1 italic">"{app.comment}"</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            </CardContent>
          </Card>

        </div>
      </div>

    </div>
  );
}
