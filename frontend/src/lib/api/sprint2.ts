import { request } from "@/lib/api-core";
import type {
  AuditLogEntry,
  ComplianceModel,
  CompliancePolicy,
  ComplianceRule,
  ExecutionRequest,
  ExecutionStatus,
  GptLabSyncResult,
  ModelValidationResult,
  PaginatedResponse,
  ValidateExecutionResponse,
} from "@/lib/types/sprint2";

export { ApiError } from "@/lib/api-core";

// Policies
export const policiesApi = {
  list: (params?: { status?: string; policy_type?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.policy_type) q.set("policy_type", params.policy_type);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<PaginatedResponse<CompliancePolicy>>(`/policies${qs ? `?${qs}` : ""}`);
  },
  listActive: () => request<PaginatedResponse<CompliancePolicy>>("/policies/active"),
  get: (id: string) => request<CompliancePolicy>(`/policies/${id}`),
  create: (body: Record<string, unknown>) =>
    request<CompliancePolicy>("/policies", { method: "POST", body: JSON.stringify(body) }),
  update: (id: string, body: Record<string, unknown>) =>
    request<CompliancePolicy>(`/policies/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  activate: (id: string) =>
    request<CompliancePolicy>(`/policies/${id}/activate`, { method: "POST" }),
  deactivate: (id: string) =>
    request<CompliancePolicy>(`/policies/${id}/deactivate`, { method: "POST" }),
  archive: (id: string) =>
    request<CompliancePolicy>(`/policies/${id}/archive`, { method: "POST" }),
  attachRules: (id: string, ruleIds: string[], sortOrder = 0) =>
    request<CompliancePolicy>(`/policies/${id}/rules`, {
      method: "POST",
      body: JSON.stringify({ rule_ids: ruleIds, sort_order: sortOrder }),
    }),
  detachRules: (id: string, ruleIds: string[]) =>
    request<CompliancePolicy>(`/policies/${id}/rules`, {
      method: "DELETE",
      body: JSON.stringify({ rule_ids: ruleIds }),
    }),
};

// Rules
export const rulesApi = {
  list: (params?: { category?: string; enabled_only?: boolean; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.enabled_only) q.set("enabled_only", "true");
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<PaginatedResponse<ComplianceRule>>(`/rules${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<ComplianceRule>(`/rules/${id}`),
  create: (body: Record<string, unknown>) =>
    request<ComplianceRule>("/rules", { method: "POST", body: JSON.stringify(body) }),
  update: (id: string, body: Record<string, unknown>) =>
    request<ComplianceRule>(`/rules/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  enable: (id: string) => request<ComplianceRule>(`/rules/${id}/enable`, { method: "POST" }),
  disable: (id: string) => request<ComplianceRule>(`/rules/${id}/disable`, { method: "POST" }),
};

// Executions
export const executionsApi = {
  list: (params?: { limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<PaginatedResponse<ExecutionRequest>>(`/executions${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<ExecutionRequest>(`/executions/${id}`),
  validate: (body: {
    dataset_id: string;
    scan_id: string;
    model_id: string;
    execution_purpose: string;
  }) =>
    request<ValidateExecutionResponse>("/executions/validate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getStatus: (id: string) => request<ExecutionStatus>(`/executions/${id}/status`),
  start: (id: string) =>
    request<{ execution_request_id: string; status: string; decision: string; message: string; started_at: string }>(
      `/executions/${id}/start`,
      { method: "POST" }
    ),
  acknowledgeWarning: (id: string, acknowledgement_note?: string) =>
    request<{
      execution_request_id: string;
      status: string;
      message: string;
      can_start: boolean;
      acknowledged_at: string;
    }>(`/executions/${id}/acknowledge-warning`, {
      method: "POST",
      body: JSON.stringify({ acknowledgement_note: acknowledgement_note ?? null }),
    }),
};

// Audit
export const auditApi = {
  list: (params?: {
    user_id?: string;
    action?: string;
    action_prefix?: string;
    severity?: string;
    status?: string;
    resource_type?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.user_id) q.set("user_id", params.user_id);
    if (params?.action) q.set("action", params.action);
    if (params?.action_prefix) q.set("action_prefix", params.action_prefix);
    if (params?.severity) q.set("severity", params.severity);
    if (params?.status) q.set("status", params.status);
    if (params?.resource_type) q.set("resource_type", params.resource_type);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<PaginatedResponse<AuditLogEntry>>(`/audit-logs${qs ? `?${qs}` : ""}`);
  },
};

// Models
export const modelsApi = {
  list: (params?: {
    active_only?: boolean;
    approved_only?: boolean;
    model_type?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.active_only === false) q.set("active_only", "false");
    if (params?.approved_only) q.set("approved_only", "true");
    if (params?.model_type) q.set("model_type", params.model_type);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<PaginatedResponse<ComplianceModel>>(`/models${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<ComplianceModel>(`/models/${id}`),
  create: (body: Record<string, unknown>) =>
    request<ComplianceModel>("/models", { method: "POST", body: JSON.stringify(body) }),
  update: (id: string, body: Record<string, unknown>) =>
    request<ComplianceModel>(`/models/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  validate: (body: { scan_id: string; model_id: string }) =>
    request<ModelValidationResult>("/models/validate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getValidation: (id: string) =>
    request<ModelValidationResult>(`/models/validations/${id}`),
  syncGptlab: (params?: {
    approve_new?: boolean;
    deactivate_demos?: boolean;
    deactivate_missing?: boolean;
  }) => {
    const q = new URLSearchParams();
    if (params?.approve_new === false) q.set("approve_new", "false");
    if (params?.deactivate_demos) q.set("deactivate_demos", "true");
    if (params?.deactivate_missing === false) q.set("deactivate_missing", "false");
    const qs = q.toString();
    return request<GptLabSyncResult>(
      `/models/sync-gptlab${qs ? `?${qs}` : ""}`,
      { method: "POST" }
    );
  },
};
