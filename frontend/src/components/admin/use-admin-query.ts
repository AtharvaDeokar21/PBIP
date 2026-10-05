"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

// Apply filters immediately and retain earlier changes while URL navigation is pending.
export function useAdminQuery(path: string) {
  const router = useRouter();
  const url = useSearchParams();
  const urlString = url.toString();
  const [params, setParams] = useState(() => new URLSearchParams(urlString));
  const current = useRef(new URLSearchParams(urlString));
  const pending = useRef<string | null>(null);
  useEffect(() => {
    if (pending.current !== null && pending.current !== urlString) return;
    pending.current = null;
    const next = new URLSearchParams(urlString);
    current.current = next;
    setParams(next);
  }, [urlString]);
  function navigate(next: URLSearchParams) {
    current.current = next;
    setParams(next);
    pending.current = next.toString();
    router.replace(`${path}${next.size ? `?${next}` : ""}`, { scroll: false });
  }
  function update(key: string, value: string) {
    const next = new URLSearchParams(current.current);
    value === "all" || !value ? next.delete(key) : next.set(key, value);
    navigate(next);
  }
  function reset() {
    navigate(new URLSearchParams());
  }
  return { params, update, reset };
}
