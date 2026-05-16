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
