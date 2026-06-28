import { request } from "@/lib/api-core";
import type { NistControlsCatalog, NistCurrentProfile } from "@/lib/types/nistAiRmf";

export const nistAiRmfApi = {
  controls() {
    return request<NistControlsCatalog>("/nist-ai-rmf/controls");
  },

  currentProfile() {
    return request<NistCurrentProfile>("/nist-ai-rmf/profile/current");
  },
};
