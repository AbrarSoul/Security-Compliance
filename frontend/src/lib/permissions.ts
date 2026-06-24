/** Permission codes aligned with backend RBAC */

export const PERMS = {
  FILE_UPLOAD: "file:upload",
  FILE_READ: "file:read",
  SCAN_RUN: "scan:run",
  SCAN_READ: "scan:read",
  REPORT_READ: "report:read",
  REPORT_READ_ALL: "report:read_all",
  EXECUTION_REQUEST: "execution:request",
  EXECUTION_READ: "execution:read",
  EXECUTION_READ_ALL: "execution:read_all",
  POLICY_MANAGE: "policy:manage",
  RULE_MANAGE: "rule:manage",
  AUDIT_READ: "audit:read",
  POLICY_VIOLATION_READ: "policy_violation:read",
  ANALYTICS_READ: "analytics:read",
  ANALYTICS_READ_ALL: "analytics:read_all",
  GAP_READ: "gap:read",
  GAP_ANALYZE: "gap:analyze",
  GAP_READ_ALL: "gap:read_all",
  THREAT_READ: "threat:read",
  THREAT_READ_ALL: "threat:read_all",
  THREAT_MANAGE: "threat:manage",
  GAIRA_READ: "gaira:read",
  GAIRA_MANAGE: "gaira:manage",
  GAIRA_READ_ALL: "gaira:read_all",
} as const;

export const ROLES = {
  ADMIN: "admin",
  USER: "user",
  AUDITOR: "auditor",
} as const;

export function hasPermission(permissions: string[], code: string): boolean {
  return permissions.includes(code);
}

export function hasAnyPermission(permissions: string[], ...codes: string[]): boolean {
  return codes.some((c) => permissions.includes(c));
}

export function hasRole(roles: string[], role: string): boolean {
  return roles.includes(role);
}

export function isAdmin(roles: string[]): boolean {
  return hasRole(roles, ROLES.ADMIN);
}

export function isAuditor(roles: string[]): boolean {
  return hasRole(roles, ROLES.AUDITOR);
}
