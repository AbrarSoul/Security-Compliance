import { IconShield } from "@/components/ui/icons";

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 flex-col justify-between border-r border-border bg-surface-sidebar p-12 lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-black shadow-glow">
            <IconShield className="h-6 w-6" />
          </div>
          <span className="text-lg font-semibold text-text-primary">ComplianceGuard</span>
        </div>
        <div>
          <h2 className="text-3xl font-bold leading-tight text-text-primary text-balance">
            Enterprise security compliance for your datasets
          </h2>
          <p className="mt-4 max-w-md text-text-muted">
            Scan, score, and report on sensitive data exposure across CSV, JSON, and text
            datasets — built for security and compliance teams.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-text-muted">
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Automated PII & credential detection
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Risk scoring & compliance classification
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Exportable PDF & JSON reports
            </li>
          </ul>
        </div>
        <p className="text-xs text-text-muted">© ComplianceGuard · Security Compliance Platform</p>
      </div>
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-md animate-fade-in-up">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-black">
                <IconShield className="h-5 w-5" />
              </div>
              <span className="font-semibold text-text-primary">ComplianceGuard</span>
            </div>
          </div>
          <div className="card-modern">
            <h1 className="text-2xl font-semibold text-text-primary">{title}</h1>
            <p className="mt-2 text-sm text-text-muted">{subtitle}</p>
            <div className="mt-8">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
