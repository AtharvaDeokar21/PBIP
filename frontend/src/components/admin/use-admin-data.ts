"use client";
import { useCallback, useEffect, useState } from "react";
import { getAdminSnapshot } from "@/lib/admin/service";
import type { AdminSnapshot } from "@/lib/admin/types";
export function useAdminData() {
  const [data, setData] = useState<AdminSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true;
    setLoading(true);
    setError("");
    getAdminSnapshot()
      .then((snapshot) => {
        if (current) setData(snapshot);
      })
      .catch(() => {
        if (current)
          setError(
            "We couldn’t load the internal workspace. Please try again.",
          );
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [revision]);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  return { data, loading, error, refresh };
}
