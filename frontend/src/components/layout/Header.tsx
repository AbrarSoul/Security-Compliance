"use client";

import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { clearSession, getStoredUser } from "@/lib/auth";
import { Button } from "@/components/ui/Button";

export function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  const router = useRouter();
  const user = getStoredUser();

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch {
      /* ignore */
    }
    clearSession();
    router.replace("/login");
    router.refresh();
  }

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <header className="glass-strong sticky top-0 z-10 flex items-center justify-between border-b border-border px-6 py-4 lg:px-8">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-text-muted">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        {user && (
          <div className="hidden items-center gap-3 sm:flex">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/20 text-sm font-semibold text-primary">
              {initials}
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-text-primary">{user.full_name || "User"}</p>
              <p className="text-xs text-text-muted">{user.email}</p>
            </div>
          </div>
        )}
        <Button variant="ghost" onClick={handleLogout}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
