import { expect, test } from "@playwright/test";
import { mockApiMe, seedAuth } from "./fixtures/auth";

test.describe("Dashboard integration (mocked API)", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuth(page, "user");
    await mockApiMe(page);

    await page.route("**/api/v1/files**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items: [], total: 0 }),
        });
      }
      return route.continue();
    });

    await page.route("**/api/v1/scans**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      })
    );

    await page.route("**/api/v1/reports**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      })
    );

    await page.route("**/api/v1/executions**", (route) => {
      if (route.request().url().includes("/validate")) return route.continue();
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "e1000001-0001-4001-8001-000000000001",
              user_id: "00000000-0000-4000-8000-000000000001",
              file_id: "f1000001-0001-4001-8001-000000000001",
              scan_id: "s1000001-0001-4001-8001-000000000001",
              compliance_model_id: "b2000001-0001-4001-8001-000000000001",
              execution_purpose: "Demo",
              model_name: "Demo Local LLM",
              model_provider: "Internal",
              status: "allowed",
              created_at: new Date().toISOString(),
              execution_result: {
                id: "r1000001-0001-4001-8001-000000000001",
                decision: "allow",
                risk_score: 15,
                risk_level: "low",
                reason_codes: [],
                status: "completed",
                created_at: new Date().toISOString(),
              },
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    await page.route("**/api/v1/policies**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "c2000001-0001-4001-8001-000000000001",
              name: "Demo Execution Baseline",
              description: "Demo",
              policy_type: "execution_policy",
              status: "active",
              priority: 10,
              thresholds: { block_below: 40, warn_below: 70 },
              is_active: true,
              severity_default: "medium",
              created_by_user_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              rules: [],
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      })
    );

    await page.route("**/api/v1/rules**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "a1000001-0001-4001-8001-000000000001",
              code: "data.email_detected",
              name: "Email detected",
              description: null,
              category: "data",
              severity: "medium",
              action: "warn",
              priority: 50,
              condition: {},
              is_enabled: true,
              created_by_user_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      })
    );

    await page.route("**/api/v1/models**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "b2000001-0001-4001-8001-000000000001",
              code: "DEMO_LOCAL_LLM",
              name: "Demo Local LLM",
              provider: "Internal",
              model_type: "local_model",
              endpoint_url: null,
              data_retention_policy: null,
              logging_enabled: false,
              data_leaves_platform: false,
              is_approved: true,
              is_active: true,
              metadata: {},
              created_by_user_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      })
    );
  });

  test("overview loads for authenticated user", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
    await expect(page.getByText("Uploaded files")).toBeVisible();
  });

  test("executions page shows history", async ({ page }) => {
    await page.goto("/executions");
    await expect(page.getByRole("heading", { name: "Execution status" })).toBeVisible();
    await expect(page.getByText("Demo Local LLM")).toBeVisible();
  });

  test("policies page lists policies", async ({ page }) => {
    await page.goto("/policies");
    await expect(page.getByRole("heading", { name: "Policy management" })).toBeVisible();
    await expect(page.getByText("Demo Execution Baseline")).toBeVisible();
  });

  test("rules page lists rules", async ({ page }) => {
    await page.goto("/rules");
    await expect(page.getByRole("heading", { name: "Rule management" })).toBeVisible();
    await expect(page.getByText("Email detected")).toBeVisible();
  });

  test("models page shows registered models", async ({ page }) => {
    await page.goto("/models");
    await expect(page.getByRole("heading", { name: "Model validation" })).toBeVisible();
    await expect(page.getByText("Demo Local LLM")).toBeVisible();
  });
});

test.describe("RBAC protected routes", () => {
  test("audit page denied for standard user", async ({ page }) => {
    await seedAuth(page, "user");
    await mockApiMe(page);
    await page.goto("/audit");
    await expect(page.getByText("Access denied")).toBeVisible();
  });

  test("audit page loads for admin", async ({ page }) => {
    await seedAuth(page, "admin");
    await mockApiMe(page, "admin");
    await page.route("**/api/v1/audit-logs**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }),
      })
    );
    await page.goto("/audit");
    await expect(page.getByRole("heading", { name: "Audit logs" })).toBeVisible();
  });
});
