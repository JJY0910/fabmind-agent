"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ApprovalDetailDrawer, type ApprovalQueueItemSummary } from "@/components/ui/approval-detail-drawer";
import {
  CodePill,
  DataSourceBanner,
  OperationalTable,
  OperationalTableBody,
  OperationalTableHeader,
  StatusBadge,
  TableStateRow,
} from "@/components/ui/operational";
import { createReferenceListResponse, fetchApprovalQueue, fetchCurrentUser, type AuthUser } from "@/lib/api";
import { FileText, CheckCircle2, Clock, User } from "lucide-react";
import Link from "next/link";

const fallbackApprovals: ApprovalQueueItemSummary[] = [
  { approval_id: "APP-001", report_draft_id: "RPT-LP-01", diagnosis_session_id: "LP-01-SESSION", equipment_code: "LP-01", approval_status: "PENDING_REVIEW", requested_by: "Engineer Kim", requested_at: new Date(Date.now() - 3600000).toISOString(), reviewed_at: null, reviewer_id: null },
  { approval_id: "APP-002", report_draft_id: "RPT-FC-11", diagnosis_session_id: "FC-11-SESSION", equipment_code: "FC-11", approval_status: "APPROVED", requested_by: "Engineer Park", requested_at: new Date(Date.now() - 7200000).toISOString(), reviewed_at: new Date(Date.now() - 3600000).toISOString(), reviewer_id: "Senior Eng Lee" },
];

type DataMode = "loading" | "live" | "reference" | "empty";

function hasApprovalAuthority(user: AuthUser | null) {
  return user?.role === "SENIOR_ENGINEER" || user?.role === "ADMIN";
}

function formatUserSession(user: AuthUser) {
  return `${user.username} (${user.role.replaceAll("_", " ")})`;
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
  const [approvals, setApprovals] = useState<ApprovalQueueItemSummary[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<ApprovalQueueItemSummary | null>(null);
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
        setApprovals(res.items as ApprovalQueueItemSummary[]);
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
        <DataSourceBanner
          mode="reference"
          message={error}
          detail="Operational API connection required for live approval queue records."
        />
      )}

      {dataMode === "live" && (
        <DataSourceBanner mode="live" message={`Backend API connected. Showing ${apiTotal} approval queue item${apiTotal === 1 ? "" : "s"}.`} />
      )}

      {dataMode === "empty" && (
        <DataSourceBanner mode="empty" message="Backend API connected. No reports are waiting for approval." />
      )}

      <div className="bg-[#111d33] border border-[#1a2c4d] text-slate-300 p-3 rounded-md text-sm mb-4">
        {currentUser ? (
          hasApprovalAuthority(currentUser) ? (
            <span>Signed in as {formatUserSession(currentUser)}. Senior/admin approval actions are available on report detail pages.</span>
          ) : (
            <span>Signed in as {formatUserSession(currentUser)}. Approval queue is read-only for field users; senior/admin role is required for final decisions.</span>
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

      <OperationalTable>
        <OperationalTableHeader>
          <tr>
            <th className="px-4 py-3 font-medium">Report Draft</th>
            <th className="px-4 py-3 font-medium">Equipment</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Requester</th>
            <th className="px-4 py-3 font-medium">Requested At</th>
            <th className="px-4 py-3 font-medium text-right">Action</th>
          </tr>
        </OperationalTableHeader>
        <OperationalTableBody>
          {loading ? (
            <TableStateRow colSpan={6} title="Loading approval queue..." detail="Checking authenticated read-only approval queue access." />
          ) : approvals.length === 0 ? (
            <TableStateRow colSpan={6} title="No items in approval queue." detail="No report records are waiting for review in the current payload." />
          ) : (
            approvals.map((app) => {
              const status = app.approval_status ?? app.status ?? "UNKNOWN";
              const key = app.approval_id ?? app.report_draft_id;
              return (
                <tr key={key ?? `${app.requested_by ?? "requester"}-${app.requested_at ?? "requested"}`} className="transition-colors hover:bg-[#111d33]/50">
                  <td className="px-4 py-3">
                    <CodePill tone="amber">{app.report_draft_id ?? "REPORT_UNAVAILABLE"}</CodePill>
                    <div className="mt-1 font-mono text-[10px] text-slate-500">{app.diagnosis_session_id ?? "Diagnosis session linked in report detail"}</div>
                  </td>
                  <td className="px-4 py-3">
                    <CodePill>{app.equipment_code ?? "See report"}</CodePill>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5 text-xs text-slate-300">
                      <User className="h-3.5 w-3.5 text-slate-500" />
                      {app.requested_by ?? "Requester unavailable"}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(app.requested_at)}
                    </div>
                    <div className="ml-4 text-slate-600">{formatTime(app.requested_at)}</div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        className="inline-flex items-center rounded border border-[#ffaa00]/30 bg-[#ffaa00]/10 px-3 py-1.5 text-xs font-medium text-[#ffaa00] transition-colors hover:bg-[#ffaa00]/15 focus:outline-none focus:ring-2 focus:ring-[#ffaa00]/40"
                        onClick={() => setSelectedApproval(app)}
                      >
                        Inspect
                      </button>
                      {app.report_draft_id ? (
                        <Link href={`/report-drafts/${app.report_draft_id}`} className="inline-flex items-center gap-1 rounded bg-[#ffaa00] px-3 py-1.5 text-xs font-bold text-black shadow-[0_0_10px_rgba(255,170,0,0.2)] transition-colors hover:bg-[#ffaa00]/90">
                          Review Draft
                        </Link>
                      ) : (
                        <span className="text-xs text-slate-600">Report link unavailable</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </OperationalTableBody>
      </OperationalTable>

      <ApprovalDetailDrawer
        approval={selectedApproval}
        currentUserRole={currentUser?.role}
        dataMode={dataMode}
        onClose={() => setSelectedApproval(null)}
      />
    </div>
  );
}
