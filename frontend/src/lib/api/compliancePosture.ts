import { request } from "@/lib/api-core";
import type { CompliancePosture } from "@/lib/types/compliancePosture";

export const compliancePostureApi = {
  get() {
    return request<CompliancePosture>("/compliance/posture");
  },
};
