const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('fabmind_access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  
  return headers;
}

export async function fetchDashboardSummary() {
  const res = await fetch(`${BASE_URL}/api/v1/dashboard/summary`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchAuditEvents() {
  const res = await fetch(`${BASE_URL}/api/v1/audit-events`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch audit events');
  return res.json();
}

export async function fetchDiagnosisSession(sessionId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/diagnosis-sessions/${sessionId}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch diagnosis session');
  return res.json();
}

export async function analyzeDiagnosisSession(sessionId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/diagnosis-sessions/${sessionId}/analyze`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to analyze diagnosis session');
  return res.json();
}

export async function fetchChecklistRun(checklistRunId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/checklist-runs/${checklistRunId}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch checklist run');
  return res.json();
}

export async function fetchReportDraft(reportDraftId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/report-drafts/${reportDraftId}`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch report draft');
  return res.json();
}

export async function updateChecklistItem(checklistRunId: string, itemId: string, payload: { status?: string, field_note?: string }) {
  const res = await fetch(`${BASE_URL}/api/v1/checklist-runs/${checklistRunId}/items/${itemId}`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update checklist item');
  return res.json();
}

export async function submitReportDraft(reportDraftId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/report-drafts/${reportDraftId}/submit`, {
    method: 'POST',
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to submit report draft');
  return res.json();
}

export async function approveReportDraft(reportDraftId: string, payload?: { comment?: string }) {
  const res = await fetch(`${BASE_URL}/api/v1/report-drafts/${reportDraftId}/approve`, {
    method: 'POST',
    headers: getHeaders(),
    body: payload ? JSON.stringify(payload) : undefined
  });
  if (!res.ok) throw new Error('Failed to approve report draft');
  return res.json();
}

export async function rejectReportDraft(reportDraftId: string, payload: { comment: string }) {
  const res = await fetch(`${BASE_URL}/api/v1/report-drafts/${reportDraftId}/reject`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to reject report draft');
  return res.json();
}

export async function fetchEquipmentList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetch(`${BASE_URL}/api/v1/equipment${query}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch equipment list');
  return res.json();
}

export async function fetchEquipmentDetail(equipmentId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/equipment/${equipmentId}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch equipment detail');
  return res.json();
}

export async function fetchIncidentList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetch(`${BASE_URL}/api/v1/incidents${query}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch incident list');
  return res.json();
}

export async function fetchIncidentDetail(incidentId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/incidents/${incidentId}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch incident detail');
  return res.json();
}

export async function fetchChecklistRunList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetch(`${BASE_URL}/api/v1/checklist-runs${query}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch checklist run list');
  return res.json();
}

export async function fetchReportDraftList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetch(`${BASE_URL}/api/v1/report-drafts${query}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch report draft list');
  return res.json();
}

export async function fetchApprovalQueue(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetch(`${BASE_URL}/api/v1/approvals${query}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch approval queue');
  return res.json();
}

export async function fetchSystemSafetySettings() {
  const res = await fetch(`${BASE_URL}/api/v1/system/safety-settings`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch system safety settings');
  return res.json();
}
