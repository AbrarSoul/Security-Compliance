import { request } from "@/lib/api-core";
import type { SecurityEventLog, SecurityThreat, ThreatDashboard, UserBehaviorItem } from "@/lib/types/threats";

export const threatsApi = {
  dashboard() {
    return request<ThreatDashboard>("/threats/dashboard");
  },

  list(params?: { severity?: string; threat_type?: string }) {
    const p = new URLSearchParams();
    if (params?.severity) p.set("severity", params.severity);
    if (params?.threat_type) p.set("threat_type", params.threat_type);
    const q = p.toString();
    return request<{ items: SecurityThreat[]; total: number }>(`/threats${q ? `?${q}` : ""}`);
  },

  events() {
    return request<{ items: SecurityEventLog[]; total: number }>("/threats/events");
  },

  behavior() {
    return request<{ items: UserBehaviorItem[] }>("/threats/behavior");
  },

  detect() {
    return request<{ threats: SecurityThreat[]; threats_found: number }>("/threats/detect", {
      method: "POST",
    });
  },

  investigate(threatId: string) {
    return request<SecurityThreat>(`/threats/${threatId}/investigate`, { method: "POST" });
  },

  resolve(threatId: string) {
    return request<SecurityThreat>(`/threats/${threatId}/resolve`, { method: "POST" });
  },
};
