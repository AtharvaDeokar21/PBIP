import Link from "next/link";
import {
  ArrowUpRight,
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Inbox,
  AlertCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import type { Risk } from "@/lib/admin/types";
export function PageTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: ReactNode;
}) {
  return (
    <div className="admin-page-title">
      <div>
        <span className="eyebrow">CREDORA · INTERNAL BANKING</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </div>
  );
}
export function StatCard({
  label,
  value,
  icon: Icon,
  note,
  href,
  tone = "purple",
}: {
  label: string;
  value: ReactNode;
  icon: LucideIcon;
  note: string;
  href?: string;
  tone?: string;
}) {
  const content = (
    <>
      <div className="admin-stat-top">
        <span>{label}</span>
        <span className={`admin-stat-icon ${tone}`}>
          <Icon size={19} />
        </span>
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
      {href && <ArrowUpRight className="admin-stat-arrow" size={16} />}
    </>
  );
  return href ? (
    <Link className="admin-stat" href={href}>
      {content}
    </Link>
  ) : (
    <div className="admin-stat">{content}</div>
  );
}
export function ChartCard({
  title,
  subtitle,
  children,
  action,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function RiskBadge({ risk }: { risk: Risk | null }) {
  if (!risk) {
    return <span className="admin-badge">—</span>;
  }
  return (
    <span className={`admin-badge risk-${risk.toLowerCase()}`}>
      <i />
      {risk}
    </span>
  );
}
export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`admin-badge status-${status.toLowerCase().replaceAll(" ", "-")}`}
    >
      {status}
    </span>
  );
}
export function SearchBar({
  value,
  onChange,
  placeholder = "Search customers by name, ID or email",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="admin-search">
      <Search size={18} />
      <input
        aria-label={placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
export function FilterDropdown({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="admin-filter">
      {label}
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((option) => (
          <option value={option.value} key={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
export function DataTable({
  headings,
  children,
  label,
}: {
  headings: string[];
  children: ReactNode;
  label: string;
}) {
  return (
    <div
      className="admin-table-scroll"
      role="region"
      aria-label={label}
      tabIndex={0}
    >
      <table>
        <thead>
          <tr>
            {headings.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
export function EmptyState({
  title = "No matching records",
  message = "Try clearing your search or adjusting the filters.",
  onReset,
}: {
  title?: string;
  message?: string;
  onReset?: () => void;
}) {
  return (
    <div className="admin-empty">
      <Inbox size={30} />
      <h3>{title}</h3>
      <p>{message}</p>
      {onReset && (
        <button className="button secondary small" onClick={onReset}>
          Clear filters
        </button>
      )}
    </div>
  );
}
export function LoadingState() {
  return (
    <div className="admin-loading" role="status">
      <RefreshCw size={22} /> Loading workspace…
      <div className="admin-skeleton-grid">
        {[0, 1, 2, 3].map((i) => (
          <span key={i} />
        ))}
      </div>
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry: () => void;
}) {
  return (
    <div className="admin-empty" role="alert">
      <AlertCircle size={30} />
      <h3>Unable to load this page</h3>
      <p>{message}</p>
      <button className="button" onClick={retry}>
        Try again
      </button>
    </div>
  );
}
export function Pagination({
  page,
  size,
  total,
  onChange,
}: {
  page: number;
  size: number;
  total: number;
  onChange: (page: number) => void;
}) {
  const count = Math.max(1, Math.ceil(total / size));
  return (
    <div className="admin-pagination">
      <span>
        {total
          ? `${(page - 1) * size + 1}–${Math.min(page * size, total)} of ${total} customers`
          : "0 customers"}
      </span>
      <div>
        <button
          className="icon-button"
          aria-label="Previous page"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft size={18} />
        </button>
        <span>
          Page {page} of {count}
        </span>
        <button
          className="icon-button"
          aria-label="Next page"
          disabled={page >= count}
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}
export function HorizontalBars({
  rows,
  money = false,
}: {
  rows: { label: string; value: number; detail?: string }[];
  money?: boolean;
}) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  return (
    <div className="admin-horizontal-bars">
      {rows.map((row, index) => (
        <div key={row.label}>
          <div>
            <span>{row.label}</span>
            <strong>
              {money
                ? new Intl.NumberFormat("en-IN", {
                    style: "currency",
                    currency: "INR",
                    maximumFractionDigits: 0,
                  }).format(row.value)
                : row.value.toLocaleString("en-IN")}
              {row.detail && <small> {row.detail}</small>}
            </strong>
          </div>
          <div className="admin-bar-track">
            <span
              style={{
                width: `${(row.value / max) * 100}%`,
                background: ["#7134a3", "#9760bb", "#b78bd1", "#d7bde6"][
                  index % 4
                ],
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
export function MiniTrend({
  rows,
  money = false,
}: {
  rows: { label: string; value: number }[];
  money?: boolean;
}) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  return (
    <div
      className="admin-trend"
      role="img"
      aria-label={rows.map((row) => `${row.label}: ${row.value}`).join(", ")}
    >
      {rows.map((row) => (
        <div key={row.label}>
          <small>
            {money ? `₹${Math.round(row.value / 1000)}k` : row.value}
          </small>
          <span style={{ height: `${(row.value / max) * 120}px` }} />
          <strong>{row.label}</strong>
        </div>
      ))}
    </div>
  );
}

export { AdminHeaderDate, useCurrentDate } from "./admin-header-date";
