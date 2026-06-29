import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { gairaApi } from "@/lib/api";

export const GAIRA_REGISTRATION_UPDATED_EVENT = "gaira-registration-updated";

export function notifyGairaRegistrationUpdated() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(GAIRA_REGISTRATION_UPDATED_EVENT));
  }
}

export function usePendingGairaReviewCount(enabled: boolean): number {
  const pathname = usePathname();
  const [count, setCount] = useState(0);

  const refresh = useCallback(() => {
    if (!enabled) {
      setCount(0);
      return;
    }
    gairaApi
      .countPendingAuditor()
      .then((res) => setCount(res.total))
      .catch(() => setCount(0));
  }, [enabled]);

  useEffect(() => {
    refresh();
    if (!enabled) return;

    const interval = window.setInterval(refresh, 60_000);
    const onUpdate = () => refresh();
    window.addEventListener(GAIRA_REGISTRATION_UPDATED_EVENT, onUpdate);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener(GAIRA_REGISTRATION_UPDATED_EVENT, onUpdate);
    };
  }, [enabled, refresh, pathname]);

  return count;
}

export function usePendingGairaApprovalCount(enabled: boolean): number {
  const pathname = usePathname();
  const [count, setCount] = useState(0);

  const refresh = useCallback(() => {
    if (!enabled) {
      setCount(0);
      return;
    }
    gairaApi
      .countPendingAdmin()
      .then((res) => setCount(res.total))
      .catch(() => setCount(0));
  }, [enabled]);

  useEffect(() => {
    refresh();
    if (!enabled) return;

    const interval = window.setInterval(refresh, 60_000);
    const onUpdate = () => refresh();
    window.addEventListener(GAIRA_REGISTRATION_UPDATED_EVENT, onUpdate);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener(GAIRA_REGISTRATION_UPDATED_EVENT, onUpdate);
    };
  }, [enabled, refresh, pathname]);

  return count;
}
