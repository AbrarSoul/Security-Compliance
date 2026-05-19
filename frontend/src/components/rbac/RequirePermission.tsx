"use client";

import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function RequirePermission({
  permission,
  anyOf,
  children,
  fallback,
}: {
  permission?: string;
  anyOf?: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { loading, hasPermission, hasAnyPermission } = useAuth();

  if (loading) {
    return (
      <div className="flex justify-center py-16" role="status">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  const allowed =
    (permission && hasPermission(permission)) ||
    (anyOf && anyOf.length > 0 && hasAnyPermission(...anyOf));

  if (!allowed) {
    return (
      fallback ?? (
        <div className="page-container">
          <Card title="Access denied">
            <p className="text-text-muted">You do not have permission to view this page.</p>
            <Link href="/" className="mt-4 inline-block">
              <Button variant="secondary">Back to overview</Button>
            </Link>
          </Card>
        </div>
      )
    );
  }

  return <>{children}</>;
}
