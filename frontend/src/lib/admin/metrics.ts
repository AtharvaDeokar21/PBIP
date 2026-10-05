import type { AdminSnapshot, Customer, Session } from "./types";
export const totalBalance = (customer: Customer) =>
  customer.accounts.reduce((sum, account) => sum + account.balance, 0);
export const activeAlerts = (data: AdminSnapshot, customerId?: string) =>
  data.alerts.filter(
    (a) =>
      a.status !== "Resolved" && (!customerId || a.customerId === customerId),
  );
export const mean = (values: number[]) =>
  values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;
export const duration = (seconds: number) =>
  `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
export const engagement = (sessions: Session[]) =>
  sessions.length
    ? Math.round(
        mean(sessions.map((s) => Math.min(100, (s.clicks / s.views) * 100))),
      )
    : 0;
export const localDate = (date: string, withTime = false) =>
  new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    ...(withTime
      ? { hour: "2-digit", minute: "2-digit" }
      : { year: "numeric" }),
  }).format(new Date(date.length === 10 ? `${date}T12:00:00+05:30` : date));
export function periodBounds(period: string, asOf: string) {
  const date = new Date(`${asOf}T12:00:00Z`);
  date.setUTCDate(
    date.getUTCDate() - (period === "7" ? 6 : period === "30" ? 29 : 89),
  );
  return { from: date.toISOString().slice(0, 10), to: asOf };
}
