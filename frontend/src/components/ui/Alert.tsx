type AlertVariant = "error" | "success" | "info";

const styles: Record<AlertVariant, string> = {
  error: "border-accent-red/40 bg-accent-red/10 text-accent-red",
  success: "border-flag-success/40 bg-flag-success/10 text-flag-success-300",
  info: "border-accent-blue/40 bg-accent-blue/10 text-flag-info-300",
};

export function Alert({
  children,
  variant = "info",
}: {
  children: React.ReactNode;
  variant?: AlertVariant;
}) {
  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm font-medium animate-fade-in ${styles[variant]}`}
    >
      {children}
    </div>
  );
}
