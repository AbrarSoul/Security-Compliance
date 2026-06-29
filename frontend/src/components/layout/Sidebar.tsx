"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { usePendingRegistrationCount } from "@/hooks/usePendingRegistrationCount";
import {
  usePendingGairaApprovalCount,
  usePendingGairaReviewCount,
} from "@/hooks/usePendingGairaRegistrationCount";
import { PERMS } from "@/lib/permissions";
import {
  IconDashboard,
  IconFiles,
  IconReports,
  IconScan,
  IconShield,
} from "@/components/ui/icons";

type NavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  show?: boolean;
  badgeCount?: number;
};

function NavSection({ title, items }: { title: string; items: NavItem[] }) {
  const pathname = usePathname();
  const visible = items.filter((i) => i.show !== false);
  if (visible.length === 0) return null;

  return (
    <>
      <p className="mb-2 mt-4 px-3 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
        {title}
      </p>
      {visible.map((link) => {
        const active =
          link.href === "/"
            ? pathname === "/"
            : pathname === link.href || pathname.startsWith(`${link.href}/`);
        const Icon = link.icon;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
              active
                ? "bg-primary/20 text-primary shadow-glow border border-border-accent"
                : "text-text-muted hover:bg-surface-sidebar-hover hover:text-text-secondary"
            }`}
          >
            <Icon
              className={`h-5 w-5 shrink-0 ${
                active ? "text-primary" : "text-text-muted group-hover:text-text-secondary"
              }`}
            />
            {link.label}
            {link.badgeCount != null && link.badgeCount > 0 && (
              <span
                className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-accent-red px-1.5 text-[10px] font-bold leading-none text-white"
                aria-label={`${link.badgeCount} pending registration${link.badgeCount === 1 ? "" : "s"}`}
              >
                {link.badgeCount > 99 ? "99+" : link.badgeCount}
              </span>
            )}
          </Link>
        );
      })}
    </>
  );
}

export function Sidebar() {
  const { hasPermission, hasAnyPermission, roles, user } = useAuth();
  const canManageUsers = hasPermission(PERMS.USER_MANAGE);
  const canReviewGaira = hasPermission(PERMS.GAIRA_REVIEW);
  const canApproveGaira = hasPermission(PERMS.GAIRA_APPROVE);
  const pendingRegistrations = usePendingRegistrationCount(canManageUsers);
  const pendingGairaReviews = usePendingGairaReviewCount(canReviewGaira);
  const pendingGairaApprovals = usePendingGairaApprovalCount(canApproveGaira);

  const platform: NavItem[] = [
    { href: "/", label: "Overview", icon: IconDashboard },
    { href: "/files", label: "Files", icon: IconFiles, show: hasPermission(PERMS.FILE_READ) },
    { href: "/scans", label: "Scans", icon: IconScan, show: hasPermission(PERMS.SCAN_READ) },
    {
      href: "/reports",
      label: "Reports",
      icon: IconReports,
      show: hasAnyPermission(PERMS.REPORT_READ, PERMS.REPORT_READ_ALL),
    },
  ];

  const compliance: NavItem[] = [
    {
      href: "/executions",
      label: "Executions",
      icon: IconShield,
      show: hasAnyPermission(
        PERMS.EXECUTION_REQUEST,
        PERMS.EXECUTION_READ,
        PERMS.EXECUTION_READ_ALL
      ),
    },
    {
      href: "/models",
      label: "Models",
      icon: IconShield,
      show: hasPermission(PERMS.SCAN_READ),
    },
  ];

  const governance: NavItem[] = [
    {
      href: "/users",
      label: "Registrations",
      icon: IconShield,
      show: canManageUsers,
      badgeCount: pendingRegistrations,
    },
    {
      href: "/compliance",
      label: "Compliance posture",
      icon: IconShield,
      show: hasAnyPermission(PERMS.GAP_READ, PERMS.GAP_READ_ALL, PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL),
    },
    {
      href: "/nist-ai-rmf",
      label: "NIST AI RMF",
      icon: IconShield,
      show: hasAnyPermission(PERMS.GAP_READ, PERMS.GAP_READ_ALL, PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL),
    },
    {
      href: "/gaira",
      label: "GAIRA",
      icon: IconShield,
      show: hasAnyPermission(PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL),
    },
    {
      href: "/gaira/reviews",
      label: "GAIRA reviews",
      icon: IconShield,
      show: canReviewGaira,
      badgeCount: pendingGairaReviews,
    },
    {
      href: "/gaira/approvals",
      label: "GAIRA approvals",
      icon: IconShield,
      show: canApproveGaira,
      badgeCount: pendingGairaApprovals,
    },
    {
      href: "/policies",
      label: "Policies",
      icon: IconShield,
      show: hasAnyPermission(PERMS.POLICY_MANAGE, PERMS.SCAN_READ),
    },
    {
      href: "/rules",
      label: "Rules",
      icon: IconShield,
      show: hasAnyPermission(PERMS.RULE_MANAGE, PERMS.SCAN_READ),
    },
  ];

  const monitoring: NavItem[] = [
    {
      href: "/analytics",
      label: "Analytics",
      icon: IconScan,
      show: hasAnyPermission(PERMS.ANALYTICS_READ, PERMS.ANALYTICS_READ_ALL),
    },
    {
      href: "/gaps",
      label: "Gap analysis",
      icon: IconShield,
      show: hasAnyPermission(PERMS.GAP_READ, PERMS.GAP_READ_ALL),
    },
    {
      href: "/threats",
      label: "Threat detection",
      icon: IconShield,
      show: hasAnyPermission(PERMS.THREAT_READ, PERMS.THREAT_READ_ALL),
    },
  ];

  const audit: NavItem[] = [
    {
      href: "/audit",
      label: "Audit logs",
      icon: IconShield,
      show: hasPermission(PERMS.AUDIT_READ),
    },
  ];

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-surface-sidebar text-text-secondary shadow-nav">
      <div className="border-b border-border px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-black shadow-glow">
            <IconShield className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight text-text-primary">
              Security Compliance
            </h1>
            <p className="text-[11px] font-medium uppercase tracking-widest text-text-muted">
              GPT-LAB SANDBOX
            </p>
          </div>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
        <NavSection title="Platform" items={platform} />
        <NavSection title="Compliance" items={compliance} />
        <NavSection title="Governance" items={governance} />
        <NavSection title="Monitoring" items={monitoring} />
        <NavSection title="Audit" items={audit} />
      </nav>
      <div className="border-t border-border p-4">
        <p className="truncate text-xs text-text-muted">{user?.email}</p>
        <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wide text-text-muted">
          {roles.join(", ") || "user"}
        </p>
      </div>
    </aside>
  );
}
