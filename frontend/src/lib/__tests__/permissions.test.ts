import { describe, expect, it } from "vitest";
import {
  hasAnyPermission,
  hasPermission,
  hasRole,
  isAdmin,
  isAuditor,
  PERMS,
} from "@/lib/permissions";

describe("permissions", () => {
  const userPerms = [
    PERMS.FILE_UPLOAD,
    PERMS.FILE_READ,
    PERMS.SCAN_RUN,
    PERMS.SCAN_READ,
    PERMS.EXECUTION_REQUEST,
  ];

  const adminPerms = [...userPerms, PERMS.POLICY_MANAGE, PERMS.RULE_MANAGE, PERMS.AUDIT_READ];

  it("checks single permission", () => {
    expect(hasPermission(userPerms, PERMS.EXECUTION_REQUEST)).toBe(true);
    expect(hasPermission(userPerms, PERMS.POLICY_MANAGE)).toBe(false);
  });

  it("checks any permission", () => {
    expect(
      hasAnyPermission(userPerms, PERMS.EXECUTION_READ, PERMS.EXECUTION_REQUEST)
    ).toBe(true);
    expect(hasAnyPermission(userPerms, PERMS.AUDIT_READ, PERMS.POLICY_MANAGE)).toBe(false);
  });

  it("identifies admin and auditor roles", () => {
    expect(isAdmin(["admin"])).toBe(true);
    expect(isAdmin(["user"])).toBe(false);
    expect(isAuditor(["auditor"])).toBe(true);
    expect(hasRole(["user", "auditor"], "auditor")).toBe(true);
  });

  it("admin has governance permissions", () => {
    expect(hasPermission(adminPerms, PERMS.POLICY_MANAGE)).toBe(true);
    expect(hasPermission(adminPerms, PERMS.RULE_MANAGE)).toBe(true);
  });
});
