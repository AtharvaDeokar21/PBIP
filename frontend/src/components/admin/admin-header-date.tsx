"use client";

import { useEffect, useState } from "react";
import { CalendarDays } from "lucide-react";
import { localDate } from "@/lib/admin/metrics";

export interface AdminHeaderDateProps {
  snapshotDate?: string | null;
}

export function useCurrentDate(): string {
  const [currentDate, setCurrentDate] = useState<string>(() => localDate());

  useEffect(() => {
    // Keep currentDate synchronized with the client's current date in Asia/Kolkata
    setCurrentDate(localDate());
    const timer = setInterval(() => {
      setCurrentDate(localDate());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  return currentDate;
}

export function AdminHeaderDate({ snapshotDate }: AdminHeaderDateProps) {
  const currentDate = useCurrentDate();

  return (
    <>
      <span className="admin-date" suppressHydrationWarning>
        <CalendarDays size={16} />
        {currentDate}
      </span>
      {snapshotDate ? (
        <span
          className="admin-date admin-snapshot-tag"
          title={`Data snapshot cutoff: ${localDate(snapshotDate)}`}
        >
          Snapshot: {localDate(snapshotDate)}
        </span>
      ) : null}
    </>
  );
}
