const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type ListSource = "api" | "fallback";
export type ApiFailureKind = "unauthorized" | "forbidden" | "network" | "http" | "invalid-json";

export class ApiClientError extends Error {
  readonly kind: ApiFailureKind;
  readonly label: string;
  readonly status?: number;
  readonly detail?: string;
  readonly cause?: unknown;

  constructor(
    message: string,
    options: {
      kind: ApiFailureKind;
      label: string;
      status?: number;
      detail?: string;
      cause?: unknown;
    },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.kind = options.kind;
    this.label = options.label;
    this.status = options.status;
    this.detail = options.detail;
    this.cause = options.cause;
  }
}

export type NormalizedListResponse<T> = {
  items: T[];
  total: number;
  limit?: number;
  offset?: number;
  source: ListSource;
};

export type AuthUser = {
  id: string;
  username: string;
  display_name?: string | null;
  role: "FIELD_ENGINEER" | "SENIOR_ENGINEER" | "ADMIN" | string;
  tenant_id: string;
};

type NormalizeListOptions = {
  allowArray?: boolean;
};

export function normalizeListResponse<T>(
  payload: unknown,
  options: NormalizeListOptions = {},
): NormalizedListResponse<T> {
  if (payload && typeof payload === "object" && Array.isArray((payload as { items?: unknown }).items)) {
    const response = payload as { items: T[]; total?: number; limit?: number; offset?: number };
    return {
      items: response.items,
      total: typeof response.total === "number" ? response.total : response.items.length,
      limit: typeof response.limit === "number" ? response.limit : undefined,
      offset: typeof response.offset === "number" ? response.offset : undefined,
      source: "api",
    };
  }

  if (options.allowArray && Array.isArray(payload)) {
    return {
      items: payload as T[],
      total: payload.length,
      source: "api",
    };
  }

  throw new Error("Malformed list response from API");
}

export function createReferenceListResponse<T>(items: T[]): NormalizedListResponse<T> {
  return {
    items,
    total: items.length,
    limit: items.length,
    offset: 0,
    source: "fallback",
  };
}

function normalizeAuthUser(payload: unknown): AuthUser {
  if (!payload || typeof payload !== "object") {
    throw new Error("Malformed current user response from API");
  }
  const user = payload as Record<string, unknown>;
  if (
    typeof user.id !== "string" ||
    typeof user.username !== "string" ||
    typeof user.role !== "string" ||
    typeof user.tenant_id !== "string"
  ) {
    throw new Error("Malformed current user response from API");
  }
  return {
    id: user.id,
    username: user.username,
    display_name: typeof user.display_name === "string" ? user.display_name : null,
    role: user.role,
    tenant_id: user.tenant_id,
  };
}

async function readErrorDetail(res: Response) {
  try {
    const contentType = res.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const body = await res.json();
      const detail = body?.detail ?? body?.message;
      if (typeof detail === "string") return detail;
      if (detail != null) return JSON.stringify(detail).slice(0, 240);
      return undefined;
    }

    const text = await res.text();
    return text ? text.slice(0, 240) : undefined;
  } catch {
    return undefined;
  }
}

async function parseJsonResponse(res: Response, label: string) {
  if (!res.ok) {
    const detail = await readErrorDetail(res);
    throw new ApiClientError(
      detail ? `${label} failed with HTTP ${res.status}: ${detail}` : `${label} failed with HTTP ${res.status}`,
      {
        kind: statusToFailureKind(res.status),
        label,
        status: res.status,
        detail,
      },
    );
  }
  try {
    return await res.json();
  } catch {
    throw new ApiClientError(`${label} returned invalid JSON`, {
      kind: "invalid-json",
      label,
    });
  }
}

async function fetchApi(path: string, label: string, init?: RequestInit) {
  try {
    return await fetch(`${BASE_URL}${path}`, init);
  } catch (cause) {
    throw new ApiClientError(`${label} failed: Network failure`, {
      kind: "network",
      label,
      cause,
    });
  }
}

function statusToFailureKind(status: number): ApiFailureKind {
  if (status === 401) return "unauthorized";
  if (status === 403) return "forbidden";
  return "http";
}

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
  const res = await fetchApi("/api/v1/dashboard/summary", "Fetch dashboard summary", {
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "Fetch dashboard summary");
}

export async function fetchAuditEvents() {
  const res = await fetchApi("/api/v1/audit-events", "Fetch audit events", {
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "Fetch audit events");
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const res = await fetchApi("/api/v1/auth/me", "Fetch current user", {
    headers: getHeaders(),
  });
  return normalizeAuthUser(await parseJsonResponse(res, "Fetch current user"));
}

export async function fetchDiagnosisSession(sessionId: string) {
  const res = await fetchApi(`/api/v1/diagnosis-sessions/${sessionId}`, "Fetch diagnosis session", {
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "Fetch diagnosis session");
}

export async function analyzeDiagnosisSession(sessionId: string) {
  const res = await fetchApi(`/api/v1/diagnosis-sessions/${sessionId}/analyze`, "Analyze diagnosis session", {
    method: 'POST',
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "Analyze diagnosis session");
}

export async function fetchChecklistRun(checklistRunId: string) {
  const res = await fetchApi(`/api/v1/checklist-runs/${checklistRunId}`, "Fetch checklist run", {
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "Fetch checklist run");
}

export async function fetchReportDraft(reportDraftId: string) {
  const res = await fetchApi(`/api/v1/report-drafts/${reportDraftId}`, "Fetch report draft", {
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "Fetch report draft");
}

export async function updateChecklistItem(checklistRunId: string, itemId: string, payload: { status?: string, field_note?: string }) {
  const res = await fetchApi(`/api/v1/checklist-runs/${checklistRunId}/items/${itemId}`, "Update checklist item", {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify(payload)
  });
  return parseJsonResponse(res, "Update checklist item");
}

export async function submitReportDraft(reportDraftId: string) {
  const res = await fetchApi(`/api/v1/report-drafts/${reportDraftId}/submit`, "Submit report draft", {
    method: 'POST',
    headers: getHeaders()
  });
  return parseJsonResponse(res, "Submit report draft");
}

export async function approveReportDraft(reportDraftId: string, payload?: { comment?: string }) {
  const res = await fetchApi(`/api/v1/report-drafts/${reportDraftId}/approve`, "Approve report draft", {
    method: 'POST',
    headers: getHeaders(),
    body: payload ? JSON.stringify(payload) : undefined
  });
  return parseJsonResponse(res, "Approve report draft");
}

export async function rejectReportDraft(reportDraftId: string, payload: { comment: string }) {
  const res = await fetchApi(`/api/v1/report-drafts/${reportDraftId}/reject`, "Reject report draft", {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(payload)
  });
  return parseJsonResponse(res, "Reject report draft");
}

export async function fetchEquipmentList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetchApi(`/api/v1/equipment${query}`, "Fetch equipment list", { headers: getHeaders() });
  return normalizeListResponse<any>(await parseJsonResponse(res, "Fetch equipment list"));
}

export async function fetchEquipmentDetail(equipmentId: string) {
  const res = await fetchApi(`/api/v1/equipment/${equipmentId}`, "Fetch equipment detail", { headers: getHeaders() });
  return parseJsonResponse(res, "Fetch equipment detail");
}

export async function fetchIncidentList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetchApi(`/api/v1/incidents${query}`, "Fetch incident list", { headers: getHeaders() });
  return normalizeListResponse<any>(await parseJsonResponse(res, "Fetch incident list"));
}

export async function fetchIncidentDetail(incidentId: string) {
  const res = await fetchApi(`/api/v1/incidents/${incidentId}`, "Fetch incident detail", { headers: getHeaders() });
  return parseJsonResponse(res, "Fetch incident detail");
}

export async function fetchChecklistRunList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetchApi(`/api/v1/checklist-runs${query}`, "Fetch checklist run list", { headers: getHeaders() });
  return normalizeListResponse<any>(await parseJsonResponse(res, "Fetch checklist run list"));
}

export async function fetchReportDraftList(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetchApi(`/api/v1/report-drafts${query}`, "Fetch report draft list", { headers: getHeaders() });
  return normalizeListResponse<any>(await parseJsonResponse(res, "Fetch report draft list"));
}

export async function fetchApprovalQueue(params?: Record<string, string>) {
  const query = params ? `?${new URLSearchParams(params).toString()}` : '';
  const res = await fetchApi(`/api/v1/approvals${query}`, "Fetch approval queue", { headers: getHeaders() });
  return normalizeListResponse<any>(await parseJsonResponse(res, "Fetch approval queue"));
}

export async function fetchSystemSafetySettings() {
  const res = await fetchApi("/api/v1/system/safety-settings", "Fetch system safety settings", { headers: getHeaders() });
  return parseJsonResponse(res, "Fetch system safety settings");
}
