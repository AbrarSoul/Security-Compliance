"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
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
          </Link>
        );
      })}
    </>
  );
}

export function Sidebar() {
  const { hasPermission, hasAnyPermission, roles, user } = useAuth();

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
              ComplianceGuard
            </h1>
            <p className="text-[11px] font-medium uppercase tracking-widest text-text-muted">
              Security Sandbox
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
