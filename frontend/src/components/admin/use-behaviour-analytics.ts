"use client";
import { useCallback, useEffect, useState } from "react";
import { fetchBehaviour, fetchFilters } from "@/lib/admin/api";
import type { BehaviourResponse, FiltersResponse } from "@/lib/admin/api";
import { getToken } from "@/lib/admin/api";

export type { BehaviourResponse, FiltersResponse };

export interface BehaviourState {
  data: BehaviourResponse | null;
  filters: FiltersResponse | null;
  loading: boolean;
  error: string;
  hasToken: boolean;
}

export function useBehaviourAnalytics(params: URLSearchParams): BehaviourState & { refresh: () => void } {
  const [data, setData] = useState<BehaviourResponse | null>(null);
  const [filters, setFilters] = useState<FiltersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);

  const hasToken = Boolean(getToken());

  useEffect(() => {
    if (!hasToken) {
      setLoading(false);
      setError("Not authenticated. Please log in.");
      return;
    }

    let active = true;
    setLoading(true);
    setError("");

    Promise.all([fetchBehaviour(params), fetchFilters()])
      .then(([b, f]) => {
        if (active) {
          setData(b);
          setFilters(f);
        }
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load analytics.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.toString(), revision, hasToken]);

  const refresh = useCallback(() => setRevision((v) => v + 1), []);

  return { data, filters, loading, error, hasToken, refresh };
}
