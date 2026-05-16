"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchApprovalQueue } from "@/lib/api";
import { FileText, CheckCircle2, Clock, ShieldAlert, User, Activity } from "lucide-react";
import Link from "next/link";

const fallbackApprovals = [
  { id: "APP-001", report_draft_id: "RPT-LP-01", diagnosis_session_id: "LP-01-SESSION", equipment_code: "LP-01", status: "PENDING_APPROVAL", requested_by: "Engineer Kim", requested_at: new Date(Date.now() - 3600000).toISOString(), reviewed_at: null, reviewer_id: null },
  { id: "APP-002", report_draft_id: "RPT-FC-11", diagnosis_session_id: "FC-11-SESSION", equipment_code: "FC-11", status: "APPROVED", requested_by: "Engineer Park", requested_at: new Date(Date.now() - 7200000).toISOString(), reviewed_at: new Date(Date.now() - 3600000).toISOString(), reviewer_id: "Senior Eng Lee" },
];

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApprovalQueue()
      .then(res => {
        if (res && res.data && Array.isArray(res.data)) {
          setApprovals(res.data);
        } else if (Array.isArray(res)) {
          setApprovals(res);
        } else {
          setApprovals(fallbackApprovals);
        }
      })
      .catch(err => {
        console.warn("Backend unavailable, using deterministic fallback fixture", err);
        setApprovals(fallbackApprovals);
        setError("Backend API unavailable. Displaying deterministic fallback fixture.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const pending = approvals.filter(a => a.status === 'PENDING_APPROVAL' || a.status === 'SUBMITTED').length;
  const approvedCount = approvals.filter(a => a.status === 'APPROVED').length;

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
        </div>
      )}

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
                approvals.map((app) => (
                  <tr key={app.id} className="hover:bg-[#111d33]/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-mono text-[#00e5ff] font-medium">{app.report_draft_id}</div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">{app.diagnosis_session_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-[#00e5ff] text-xs bg-[#00e5ff]/10 w-fit px-2 py-0.5 rounded border border-[#00e5ff]/20">{app.equipment_code}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                        app.status === 'PENDING_APPROVAL' || app.status === 'SUBMITTED' ? 'bg-[#ffaa00]/10 text-[#ffaa00] border-[#ffaa00]/30' :
                        app.status === 'APPROVED' ? 'bg-[#00cc66]/10 text-[#00cc66] border-[#00cc66]/30' :
                        'bg-[#ff3366]/10 text-[#ff3366] border-[#ff3366]/30'
                      }`}>
                        {app.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 text-xs text-slate-300">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        {app.requested_by}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      <div className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(app.requested_at).toLocaleDateString()}</div>
                      <div className="text-slate-600 ml-4">{new Date(app.requested_at).toLocaleTimeString()}</div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/report-drafts/${app.report_draft_id}`} className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#ffaa00] hover:bg-[#ffaa00]/90 text-black rounded text-xs font-bold transition-colors shadow-[0_0_10px_rgba(255,170,0,0.2)]">
                        Review Draft
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
