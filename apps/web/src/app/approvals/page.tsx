"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createReferenceListResponse, fetchApprovalQueue, fetchCurrentUser, type AuthUser } from "@/lib/api";
import { FileText, CheckCircle2, Clock, User } from "lucide-react";
import Link from "next/link";

const fallbackApprovals = [
  { approval_id: "APP-001", report_draft_id: "RPT-LP-01", diagnosis_session_id: "LP-01-SESSION", equipment_code: "LP-01", approval_status: "PENDING_REVIEW", requested_by: "Engineer Kim", requested_at: new Date(Date.now() - 3600000).toISOString(), reviewed_at: null, reviewer_id: null },
  { approval_id: "APP-002", report_draft_id: "RPT-FC-11", diagnosis_session_id: "FC-11-SESSION", equipment_code: "FC-11", approval_status: "APPROVED", requested_by: "Engineer Park", requested_at: new Date(Date.now() - 7200000).toISOString(), reviewed_at: new Date(Date.now() - 3600000).toISOString(), reviewer_id: "Senior Eng Lee" },
];

type DataMode = "loading" | "live" | "reference" | "empty";

function hasApprovalAuthority(user: AuthUser | null) {
  return user?.role === "SENIOR_ENGINEER" || user?.role === "ADMIN";
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleDateString();
}

function formatTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString();
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [apiTotal, setApiTotal] = useState(0);
  const [dataMode, setDataMode] = useState<DataMode>("loading");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentUser()
      .then(user => {
        setCurrentUser(user);
        setPermissionError(null);
      })
      .catch(err => {
        console.warn("Approval permissions unavailable", err);
        setCurrentUser(null);
        setPermissionError("Approval permissions unavailable. Senior/admin role required on report detail for final decisions.");
      });
  }, []);

  useEffect(() => {
    fetchApprovalQueue()
      .then(res => {
        setApprovals(res.items);
        setApiTotal(res.total);
        setDataMode(res.items.length > 0 ? "live" : "empty");
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic reference data", err);
        const reference = createReferenceListResponse(fallbackApprovals);
        const message = err instanceof Error ? err.message : "Backend API unavailable";
        setApprovals(reference.items);
        setApiTotal(reference.total);
        setDataMode("reference");
        setError(`${message}. Showing deterministic reference data.`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const pending = approvals.filter(a => (a.approval_status ?? a.status) === 'PENDING_REVIEW' || (a.approval_status ?? a.status) === 'SUBMITTED').length;
  const approvedCount = approvals.filter(a => (a.approval_status ?? a.status) === 'APPROVED').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <FileText className="w-8 h-8 text-[#ffaa00]" />
          Approval Queue
        </h1>
        <p className="text-slate-400">
          Review and approve finalized diagnostic reports and maintenance recommendations.
        </p>
      </div>

      {error && (
        <div className="bg-[#ffaa00]/10 border border-[#ffaa00]/30 text-[#ffaa00] p-3 rounded-md text-sm mb-4">
          {error}
          <span className="block text-xs text-[#ffaa00]/80 mt-1">Operational API connection required for live approval queue records.</span>
        </div>
      )}

      {dataMode === "live" && (
        <div className="bg-[#00cc66]/10 border border-[#00cc66]/30 text-[#00cc66] p-3 rounded-md text-sm mb-4">
          Backend API connected. Showing {apiTotal} approval queue item{apiTotal === 1 ? "" : "s"}.
        </div>
      )}

      {dataMode === "empty" && (
        <div className="bg-[#111d33] border border-[#1a2c4d] text-slate-300 p-3 rounded-md text-sm mb-4">
          Backend API connected. No reports are waiting for approval.
        </div>
      )}

      <div className="bg-[#111d33] border border-[#1a2c4d] text-slate-300 p-3 rounded-md text-sm mb-4">
        {currentUser ? (
          hasApprovalAuthority(currentUser) ? (
            <span>Signed in as {currentUser.display_name ?? currentUser.username}. Senior/admin approval actions are available on report detail pages.</span>
          ) : (
            <span>Signed in as {currentUser.display_name ?? currentUser.username}. Approval queue is read-only for field users; senior/admin role is required for final decisions.</span>
          )
        ) : (
          <span>{permissionError ?? "Approval permissions unavailable."}</span>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-[#ffaa00]/5 border-[#ffaa00]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#ffaa00]">Pending Approvals</span>
              <Clock className="w-4 h-4 text-[#ffaa00]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : pending}</div>
          </CardContent>
        </Card>
        <Card className="bg-[#00cc66]/5 border-[#00cc66]/30">
          <CardContent className="p-6">
            <div className="flex justify-between items-center pb-2">
              <span className="text-sm font-medium text-[#00cc66]">Recently Approved</span>
              <CheckCircle2 className="w-4 h-4 text-[#00cc66]" />
            </div>
            <div className="text-3xl font-bold text-white mt-2">{loading ? "-" : approvedCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card className="border-[#1a2c4d] overflow-hidden bg-[#0a1322]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-[#111d33] border-b border-[#1a2c4d] text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Report Draft</th>
                <th className="px-4 py-3 font-medium">Equipment</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Requester</th>
                <th className="px-4 py-3 font-medium">Requested At</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a2c4d]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading approval queue...</td>
                </tr>
              ) : approvals.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No items in approval queue.</td>
                </tr>
              ) : (
                approvals.map((app) => {
                  const status = app.approval_status ?? app.status ?? "UNKNOWN";
                  const key = app.approval_id ?? app.report_draft_id;
                  return (
                  <tr key={key} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-mono text-[#00e5ff] font-medium">{app.report_draft_id}</div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">{app.diagnosis_session_id ?? "Diagnosis session linked in report detail"}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-[#00e5ff] text-xs bg-[#00e5ff]/10 w-fit px-2 py-0.5 rounded border border-[#00e5ff]/20">{app.equipment_code ?? "See report"}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                        status === 'PENDING_REVIEW' || status === 'SUBMITTED' ? 'bg-[#ffaa00]/10 text-[#ffaa00] border-[#ffaa00]/30' :
                        status === 'APPROVED' ? 'bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30' :
                        'bg-[#ff3366]/10 text-[#ff3366] border-[#ff3366]/30'
                      }`}>
                        {status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 text-xs text-slate-300">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        {app.requested_by}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      <div className="flex items-center gap-1"><Clock className="w-3 h-3" /> {formatDate(app.requested_at)}</div>
                      <div className="text-slate-600 ml-4">{formatTime(app.requested_at)}</div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {app.report_draft_id ? (
                        <Link href={`/report-drafts/${app.report_draft_id}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#ffaa00] hover:bg-[#ffaa00]/90 text-black rounded text-xs font-bold transition-colors shadow-[0_0_10px_rgba(255,170,0,0.2)]">
                          Review Draft
                        </Link>
                      ) : (
                        <span className="text-xs text-slate-600">Report link unavailable</span>
                      )}
                    </td>
                  </tr>
                )})
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
