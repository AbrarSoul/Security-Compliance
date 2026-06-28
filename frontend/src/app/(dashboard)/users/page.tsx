"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { EmptyState } from "@/components/ui/EmptyState";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { Select } from "@/components/forms/Select";
import { usersApi, ApiError } from "@/lib/api";
import { notifyRegistrationsUpdated } from "@/hooks/usePendingRegistrationCount";
import { PERMS, ROLES } from "@/lib/permissions";
import type { PendingUser } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const ROLE_OPTIONS = [
  { value: ROLES.USER, label: "User" },
  { value: ROLES.AUDITOR, label: "Auditor" },
  { value: ROLES.ADMIN, label: "Admin" },
];

export default function UsersPage() {
  return (
    <RequirePermission permission={PERMS.USER_MANAGE}>
      <UsersContent />
    </RequirePermission>
  );
}

function UsersContent() {
  const [pending, setPending] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [roleByUser, setRoleByUser] = useState<Record<string, string>>({});
  const [actingId, setActingId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    usersApi
      .listPending()
      .then((res) => {
        setPending(res.items);
        setRoleByUser((prev) => {
          const next = { ...prev };
          for (const user of res.items) {
            if (!next[user.id]) next[user.id] = ROLES.USER;
          }
          return next;
        });
        notifyRegistrationsUpdated();
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function approve(userId: string) {
    const role = (roleByUser[userId] ?? ROLES.USER) as "admin" | "user" | "auditor";
    setActingId(userId);
    setError("");
    setMessage("");
    try {
      const res = await usersApi.approve(userId, role);
      setMessage(res.message);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Approval failed");
    } finally {
      setActingId(null);
    }
  }

  async function reject(userId: string) {
    if (!confirm("Reject this registration request?")) return;
    setActingId(userId);
    setError("");
    setMessage("");
    try {
      const res = await usersApi.reject(userId);
      setMessage(res.message);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Rejection failed");
    } finally {
      setActingId(null);
    }
  }

  return (
    <>
      <Header
        title="User registrations"
        subtitle="Review signup requests and assign roles before users can sign in"
      />
      <div className="page-container space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}
        <Card title="Pending approval">
          {loading ? (
            <TableSkeleton rows={4} />
          ) : pending.length === 0 ? (
            <EmptyState
              title="No pending registrations"
              description="New signups will appear here until you approve or reject them."
            />
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Requested</th>
                    <th>Role</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pending.map((user) => (
                    <tr key={user.id}>
                      <td className="font-medium text-text-primary">
                        {user.full_name || "—"}
                      </td>
                      <td>{user.email}</td>
                      <td className="text-text-muted">{formatDate(user.created_at)}</td>
                      <td>
                        <Select
                          value={roleByUser[user.id] ?? ROLES.USER}
                          onChange={(e) =>
                            setRoleByUser((prev) => ({
                              ...prev,
                              [user.id]: e.target.value,
                            }))
                          }
                          disabled={actingId === user.id}
                        >
                          {ROLE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </Select>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <Button
                            loading={actingId === user.id}
                            disabled={!!actingId}
                            onClick={() => approve(user.id)}
                          >
                            Approve
                          </Button>
                          <Button
                            variant="ghost"
                            disabled={!!actingId}
                            onClick={() => reject(user.id)}
                          >
                            Reject
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
