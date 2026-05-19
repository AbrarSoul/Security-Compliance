import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, request } from "@/lib/api-core";

vi.mock("@/lib/auth", () => ({
  getAccessToken: () => "test-token",
  getRefreshToken: () => null,
  saveSession: vi.fn(),
  clearSession: vi.fn(),
}));

describe("api-core request", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("parses JSON success responses", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ items: [], total: 0 }),
    } as Response);

    const data = await request<{ total: number }>("/policies");
    expect(data.total).toBe(0);
  });

  it("throws ApiError with detail from response", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Missing permissions: policy:manage" }),
    } as Response);

    await expect(request("/policies", { method: "POST" })).rejects.toMatchObject({
      status: 403,
      message: "Missing permissions: policy:manage",
    });
  });

  it("handles structured error wrapper", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({
        detail: "Forbidden",
        error: { code: 403, message: "Forbidden", type: "http_error" },
      }),
    } as Response);

    try {
      await request("/admin");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(403);
    }
  });
});
