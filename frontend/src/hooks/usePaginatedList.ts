"use client";

import { useCallback, useEffect, useState } from "react";
import type { PaginatedResponse } from "@/lib/types/sprint2";
import { ApiError } from "@/lib/api-core";

export function usePaginatedList<T>(
  fetchPage: (offset: number, limit: number) => Promise<PaginatedResponse<T>>,
  deps: unknown[] = [],
  pageSize = 20
) {
  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchPage(offset, pageSize)
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        const msg = err instanceof ApiError ? err.message : "Failed to load data";
        setError(msg);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset, pageSize, ...deps]);

  useEffect(() => {
    reload();
  }, [reload]);

  const resetPage = useCallback(() => setOffset(0), []);

  return {
    items,
    total,
    offset,
    setOffset,
    limit: pageSize,
    loading,
    error,
    reload,
    resetPage,
  };
}
