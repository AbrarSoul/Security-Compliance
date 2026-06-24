import { request } from "@/lib/api-core";
import type {
  AIApplication,
  GairaAssessment,
  GairaFramework,
  GairaModuleDetail,
  RoaiaRow,
} from "@/lib/types/gaira";

export const gairaApi = {
  getFramework: () => request<GairaFramework>("/gaira/framework"),

  getModule: (moduleKey: string) =>
    request<GairaModuleDetail>(`/gaira/framework/${moduleKey}`),

  listRoaia: (params?: { active_only?: boolean; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.active_only === false) q.set("active_only", "false");
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<{ items: RoaiaRow[]; total: number }>(`/gaira/roaia${qs ? `?${qs}` : ""}`);
  },

  listApplications: (params?: { active_only?: boolean; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.active_only === false) q.set("active_only", "false");
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<{ items: AIApplication[]; total: number; limit: number; offset: number }>(
      `/gaira/applications${qs ? `?${qs}` : ""}`
    );
  },

  getApplication: (id: string) => request<AIApplication>(`/gaira/applications/${id}`),

  createApplication: (body: Record<string, unknown>) =>
    request<AIApplication>("/gaira/applications", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateApplication: (id: string, body: Record<string, unknown>) =>
    request<AIApplication>(`/gaira/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  listAssessments: (applicationId: string) =>
    request<{ items: GairaAssessment[]; total: number }>(
      `/gaira/applications/${applicationId}/assessments`
    ),

  getAssessment: (id: string) => request<GairaAssessment>(`/gaira/assessments/${id}`),

  startAssessment: (
    applicationId: string,
    body: { assessment_type: string; scan_id?: string }
  ) =>
    request<GairaAssessment>(`/gaira/applications/${applicationId}/assessments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateAnswers: (assessmentId: string, answers: Record<string, unknown>, merge = true) =>
    request<GairaAssessment>(`/gaira/assessments/${assessmentId}/answers`, {
      method: "PATCH",
      body: JSON.stringify({ answers, merge }),
    }),

  compute: (assessmentId: string) =>
    request<GairaAssessment>(`/gaira/assessments/${assessmentId}/compute`, {
      method: "POST",
    }),

  submit: (
    assessmentId: string,
    body: {
      overall_risk_level?: string;
      proceed_decision?: string;
      decision_comments?: string;
    }
  ) =>
    request<GairaAssessment>(`/gaira/assessments/${assessmentId}/submit`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
