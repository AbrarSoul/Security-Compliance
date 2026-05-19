import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const SPRINT3_PERMISSIONS = [
  "file:read",
  "scan:read",
  "report:read",
  "execution:request",
  "execution:read",
  "monitoring:read",
  "monitoring:publish",
  "monitoring:manage",
  "notification:read",
  "notification:manage",
  "analytics:read",
  "gap:read",
  "threat:read",
];

const SPRINT3_USER = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "sprint3@compliance.test",
  full_name: "Sprint3 User",
  is_active: true,
  created_at: new Date().toISOString(),
  roles: ["user"],
  permissions: SPRINT3_PERMISSIONS,
};

async function seedSprint3Auth(page: Page) {
  await page.addInitScript((u) => {
    localStorage.setItem("compliance_access_token", "playwright-test-token");
    localStorage.setItem("compliance_refresh_token", "playwright-refresh-token");
    localStorage.setItem("compliance_user", JSON.stringify(u));
    localStorage.setItem(
      "compliance_rbac",
      JSON.stringify({ roles: u.roles, permissions: u.permissions })
    );
  }, SPRINT3_USER);

  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(SPRINT3_USER),
    })
  );
}

const emptyDashboard = {
  open_threats: [],
  open_total: 0,
  by_severity: {},
  by_type: {},
  security_posture: 100,
  latest_run: null,
};

const emptyAnalytics = {
  summary: {
    violation_events: 0,
    blocked_executions: 0,
    policy_violations: 0,
    prompt_scans_total: 0,
    prompt_blocked: 0,
    output_scans_total: 0,
    output_blocked: 0,
    avg_prompt_risk: null,
    avg_output_risk: null,
    unread_notifications: 0,
    scope: "user",
  },
  execution_trend: [],
  risk_trend: [],
  violation_trend: [],
  policy_violation_trend: [],
  prompt_stats: {
    total_scans: 0,
    blocked: 0,
    warned: 0,
    allowed: 0,
    decision_breakdown: [],
    avg_risk_score: null,
  },
  output_stats: {
    total_scans: 0,
    blocked: 0,
    warned: 0,
    leakage_breakdown: [],
    avg_risk_score: null,
  },
  blocked_executions: { total_blocked: 0, status_breakdown: [], trend: [] },
  realtime_violations: [],
  high_risk_users: [],
  high_risk_models: [],
  guard_actions: [],
};

test.describe("Sprint 3 dashboard routes (mocked API)", () => {
  test.beforeEach(async ({ page }) => {
    await seedSprint3Auth(page);

    await page.route("**/api/v1/analytics/dashboard**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(emptyAnalytics),
      })
    );

    await page.route("**/api/v1/gaps/dashboard**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          latest_run: null,
          open_gaps: [],
          open_total: 0,
          by_severity: {},
          by_category: {},
          posture_score: 100,
          last_analyzed_at: null,
        }),
      })
    );

    await page.route("**/api/v1/threats/dashboard**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(emptyDashboard),
      })
    );

    await page.route("**/api/v1/threats/events**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, limit: 50, offset: 0 }),
      })
    );
  });

  test("analytics page loads", async ({ page }) => {
    await page.goto("/analytics");
    await expect(page.getByRole("heading", { name: "Analytics & monitoring" })).toBeVisible();
    await expect(page.getByText("Violation events")).toBeVisible();
  });

  test("gaps page loads", async ({ page }) => {
    await page.goto("/gaps");
    await expect(page.getByRole("heading", { name: "Compliance gap analysis" })).toBeVisible();
    await expect(page.getByText("Posture score")).toBeVisible();
  });

  test("threats page loads", async ({ page }) => {
    await page.goto("/threats");
    await expect(page.getByRole("heading", { name: "Security monitoring" })).toBeVisible();
    await expect(page.getByText("Security posture")).toBeVisible();
  });
});
