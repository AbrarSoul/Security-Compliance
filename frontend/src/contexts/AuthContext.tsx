"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { authApi } from "@/lib/api";
import { getStoredUser, saveSession, clearSession, getAccessToken } from "@/lib/auth";
import {
  hasAnyPermission,
  hasPermission,
  hasRole,
  isAdmin,
  isAuditor,
} from "@/lib/permissions";
import type { User, UserMe } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  roles: string[];
  permissions: string[];
  loading: boolean;
  refreshUser: () => Promise<void>;
  hasPermission: (code: string) => boolean;
  hasAnyPermission: (...codes: string[]) => boolean;
  hasRole: (role: string) => boolean;
  isAdmin: boolean;
  isAuditor: boolean;
  canManagePolicies: boolean;
  canManageRules: boolean;
  canRequestExecution: boolean;
  canReadAudit: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const applyMe = useCallback((me: UserMe) => {
    setUser(me);
    setRoles(me.roles ?? []);
    setPermissions(me.permissions ?? []);
    localStorage.setItem(
      "compliance_user",
      JSON.stringify({ ...me, roles: me.roles, permissions: me.permissions })
    );
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await authApi.me();
    applyMe(me);
  }, [applyMe]);

  useEffect(() => {
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    const stored = getStoredUser();
    if (stored) setUser(stored);
    authApi
      .me()
      .then(applyMe)
      .catch(() => {
        const raw = localStorage.getItem("compliance_rbac");
        if (raw) {
          try {
            const rbac = JSON.parse(raw) as { roles: string[]; permissions: string[] };
            setRoles(rbac.roles);
            setPermissions(rbac.permissions);
          } catch {
            /* ignore */
          }
        }
      })
      .finally(() => setLoading(false));
  }, [applyMe]);

  useEffect(() => {
    if (roles.length || permissions.length) {
      localStorage.setItem("compliance_rbac", JSON.stringify({ roles, permissions }));
    }
  }, [roles, permissions]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      roles,
      permissions,
      loading,
      refreshUser,
      hasPermission: (code) => hasPermission(permissions, code),
      hasAnyPermission: (...codes) => hasAnyPermission(permissions, ...codes),
      hasRole: (role) => hasRole(roles, role),
      isAdmin: isAdmin(roles),
      isAuditor: isAuditor(roles),
      canManagePolicies: hasPermission(permissions, "policy:manage"),
      canManageRules: hasPermission(permissions, "rule:manage"),
      canRequestExecution: hasPermission(permissions, "execution:request"),
      canReadAudit: hasPermission(permissions, "audit:read"),
    }),
    [user, roles, permissions, loading, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
