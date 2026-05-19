import type { Page } from "@playwright/test";

const DEMO_USER = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "demo@compliance.test",
  full_name: "Demo User",
  is_active: true,
  created_at: new Date().toISOString(),
  roles: ["user"],
  permissions: [
    "file:upload",
    "file:read",
    "scan:run",
    "scan:read",
    "report:read",
    "execution:request",
    "execution:read",
  ],
};

const ADMIN_USER = {
  ...DEMO_USER,
  email: "admin@compliance.test",
  full_name: "Demo Admin",
  roles: ["admin"],
  permissions: [
    ...DEMO_USER.permissions,
    "policy:manage",
    "rule:manage",
    "execution:read_all",
    "audit:read",
    "report:read_all",
    "user:manage",
  ],
};

export async function seedAuth(page: Page, variant: "user" | "admin" = "user") {
  const user = variant === "admin" ? ADMIN_USER : DEMO_USER;
  await page.addInitScript((u) => {
    localStorage.setItem("compliance_access_token", "playwright-test-token");
    localStorage.setItem("compliance_refresh_token", "playwright-refresh-token");
    localStorage.setItem("compliance_user", JSON.stringify(u));
    localStorage.setItem(
      "compliance_rbac",
      JSON.stringify({ roles: u.roles, permissions: u.permissions })
    );
  }, user);
}

export async function mockApiMe(page: Page, variant: "user" | "admin" = "user") {
  const user = variant === "admin" ? ADMIN_USER : DEMO_USER;
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(user),
    })
  );
}
