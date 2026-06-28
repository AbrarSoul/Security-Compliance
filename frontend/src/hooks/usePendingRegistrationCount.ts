import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { usersApi } from "@/lib/api";

export const REGISTRATIONS_UPDATED_EVENT = "registrations-updated";

export function notifyRegistrationsUpdated() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(REGISTRATIONS_UPDATED_EVENT));
  }
}

export function usePendingRegistrationCount(enabled: boolean): number {
  const pathname = usePathname();
  const [count, setCount] = useState(0);

  const refresh = useCallback(() => {
    if (!enabled) {
      setCount(0);
      return;
    }
    usersApi
      .listPending()
      .then((res) => setCount(res.total))
      .catch(() => setCount(0));
  }, [enabled]);

  useEffect(() => {
    refresh();
    if (!enabled) return;

    const interval = window.setInterval(refresh, 60_000);
    const onUpdate = () => refresh();
    window.addEventListener(REGISTRATIONS_UPDATED_EVENT, onUpdate);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener(REGISTRATIONS_UPDATED_EVENT, onUpdate);
    };
  }, [enabled, refresh, pathname]);

  return count;
}
