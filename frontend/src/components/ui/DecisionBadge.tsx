import { Badge } from "./Badge";
import { decisionVariant, flagVariant, statusLabel } from "@/lib/utils";

export function DecisionBadge({ decision }: { decision: string | null | undefined }) {
  if (!decision) return <Badge variant="neutral">Unknown</Badge>;
  return <Badge variant={decisionVariant(decision)}>{decision.toUpperCase()}</Badge>;
}

export function StatusBadge({ status }: { status: string | null | undefined }) {
  return <Badge variant={flagVariant(status)}>{statusLabel(status)}</Badge>;
}
