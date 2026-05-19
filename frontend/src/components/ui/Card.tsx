export function Card({
  title,
  description,
  action,
  children,
  className = "",
  modern = true,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  modern?: boolean;
}) {
  const base = modern
    ? "card-modern animate-fade-in-up"
    : "rounded-lg border border-border bg-surface p-6 animate-fade-in-up";

  return (
    <div className={`${base} ${className}`}>
      {(title || action) && (
        <div className="-mx-6 -mt-6 mb-6 flex items-start justify-between gap-4 border-b border-border px-6 py-4">
          <div>
            {title && <h2 className="text-base font-semibold text-text-primary">{title}</h2>}
            {description && <p className="mt-0.5 text-sm text-text-muted">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
