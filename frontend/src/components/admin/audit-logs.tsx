"use client";
import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import {
  FileText,
  Shield,
  RefreshCw,
  Download,
  Filter,
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
  Edit,
  LogIn,
  LogOut,
  Key,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useAdminData } from "./use-admin-data";
import {
  PageTitle,
  AdminHeaderDate,
  ChartCard,
  DataTable,
  FilterDropdown,
  SearchBar,
  EmptyState,
  LoadingState,
  ErrorState,
  StatCard,
  Pagination,
} from "./ui";
import { localDate } from "@/lib/admin/metrics";
import type { AuditEntry, AuditSummary } from "@/lib/admin/types";
import { fetchAuditLogs, exportAllAuditLogs } from "@/lib/admin/api";

const ACTION_ICONS: Record<string, LucideIcon> = {
  Login: LogIn,
  Logout: LogOut,
  "Profile update": Edit,
  "Password change": Key,
  "Account view": Eye,
  "Transaction view": Eye,
  "Alert review": AlertCircle,
  "Alert resolved": CheckCircle,
  "Customer registered": Edit,
  "Transfer created": CheckCircle,
  "Transfer completed": CheckCircle,
  "Transfer cancelled": AlertCircle,
  "Bill payment": CheckCircle,
  "Payee created": Edit,
  "Payee updated": Edit,
  "Payee deactivated": AlertCircle,
  "Investment purchase": CheckCircle,
  "Loan application": Edit,
};

const PAGE_SIZE = 15;

/**
 * Escapes a cell value for RFC 4180 CSV compliance and protects against
 * spreadsheet formula injection (CWE-1236 / CSV injection).
 */
function escapeCsvCell(value: unknown): string {
  if (value === null || value === undefined) {
    return '""';
  }
  let str = String(value);

  // Formula injection defense: if value begins with =, +, -, @, \t, or \r,
  // prepend a single quote to force spreadsheet programs (Excel, Calc, Sheets) to treat it as text.
  const formulaTriggers = ["=", "+", "-", "@", "\t", "\r"];
  if (formulaTriggers.some((trigger) => str.startsWith(trigger))) {
    str = `'${str}`;
  }

  // Standard CSV escaping: double any embedded double-quotes and enclose the cell in quotes.
  const escaped = str.replace(/"/g, '""');
  return `"${escaped}"`;
}

export default function AuditLogs() {
  const { data, loading: adminLoading, error: adminError, refresh: refreshAdmin } =
    useAdminData();
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsError, setLogsError] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [actor, setActor] = useState("all");
  const [action, setAction] = useState("all");
  const [outcome, setOutcome] = useState("all");
  const [page, setPage] = useState(1);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  // Debounce search input to avoid requests on every keystroke
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  // Server-side filtered and paginated fetch
  const loadAuditLogs = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;
    setLogsLoading(true);
    setLogsError("");

    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    });

    if (actor !== "all") params.set("actor", actor);
    if (action !== "all") params.set("action", action);
    if (outcome !== "all") params.set("outcome", outcome);
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());

    try {
      const res = await fetchAuditLogs(params);
      if (currentRequestId === requestIdRef.current) {
        setLogs(res.items);
        setTotal(res.total);
        setSummary(res.summary);
      }
    } catch (err: unknown) {
      if (currentRequestId === requestIdRef.current) {
        setLogsError(
          err instanceof Error
            ? err.message
            : "Failed to load audit logs from server.",
        );
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLogsLoading(false);
      }
    }
  }, [page, actor, action, outcome, debouncedSearch]);

  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  const refreshAll = useCallback(() => {
    refreshAdmin();
    loadAuditLogs();
  }, [refreshAdmin, loadAuditLogs]);

  function resetFilters() {
    setSearch("");
    setDebouncedSearch("");
    setActor("all");
    setAction("all");
    setOutcome("all");
    setPage(1);
  }

  // Client-side CSV export of ALL records matching current filters across pages
  const handleExportCsv = useCallback(async () => {
    if (total === 0 || isExporting) return;
    setIsExporting(true);
    setExportProgress("Preparing export...");
    setExportError(null);

    try {
      // Build query params for currently active search and filters (without pagination)
      const exportParams = new URLSearchParams();
      if (actor !== "all") exportParams.set("actor", actor);
      if (action !== "all") exportParams.set("action", action);
      if (outcome !== "all") exportParams.set("outcome", outcome);
      if (debouncedSearch.trim()) exportParams.set("search", debouncedSearch.trim());

      const allLogs = await exportAllAuditLogs(
        exportParams,
        (loaded, totalCount) => {
          setExportProgress(`Exporting (${loaded}/${totalCount})...`);
        },
      );

      if (allLogs.length === 0) {
        setExportError("No matching records found to export.");
        return;
      }

      const headers = [
        "Log ID",
        "Actor",
        "Role",
        "Action",
        "Resource",
        "Resource ID",
        "Outcome",
        "IP Address",
        "Timestamp",
      ];

      const rows = allLogs.map((log) => [
        escapeCsvCell(log.id),
        escapeCsvCell(log.actor),
        escapeCsvCell(log.actorRole),
        escapeCsvCell(log.action),
        escapeCsvCell(log.resource),
        escapeCsvCell(log.resourceId),
        escapeCsvCell(log.outcome),
        escapeCsvCell(log.ipAddress),
        escapeCsvCell(log.timestamp),
      ]);

      const csvContent =
        "\uFEFF" +
        [headers.map(escapeCsvCell).join(","), ...rows.map((e) => e.join(","))].join("\r\n");

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setExportError(
        err instanceof Error
          ? `Export failed: ${err.message}`
          : "Failed to export audit logs. Please try again.",
      );
    } finally {
      setIsExporting(false);
      setExportProgress(null);
    }
  }, [total, isExporting, actor, action, outcome, debouncedSearch]);

  const actors = useMemo(() => {
    const list = summary?.availableActors ?? [];
    if (list.length > 0) return list;
    return Array.from(new Set(logs.map((l) => l.actor))).filter(Boolean);
  }, [summary, logs]);

  const actions = useMemo(() => {
    const list = summary?.availableActions ?? [];
    if (list.length > 0) return list;
    return Array.from(new Set(logs.map((l) => l.action))).filter(Boolean);
  }, [summary, logs]);

  if (adminLoading) return <LoadingState />;
  if (adminError || !data)
    return <ErrorState message={adminError} retry={refreshAll} />;

  const totalEvents = summary?.totalEvents ?? total;
  const successCount = summary?.successCount ?? total;
  const failureCount = summary?.failureCount ?? 0;
  const warningCount = summary?.warningCount ?? 0;

  return (
    <>
      <PageTitle
        title="Audit Logs"
        subtitle="Complete record of all internal workspace actions, access events and system changes."
        action={
          <div className="admin-title-actions">
            <AdminHeaderDate />
            <button className="button secondary small" onClick={refreshAll}>
              <RefreshCw size={15} /> Refresh
            </button>
          </div>
        }
      />

      <div className="admin-overview-banner">
        <div>
          <span className="admin-banner-icon">
            <FileText size={28} />
          </span>
          <div>
            <h2>Complete audit trail for your workspace.</h2>
            <p>
              {totalEvents} events recorded · {failureCount} failed attempts ·{" "}
              {warningCount} warnings requiring review.
            </p>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
          <button
            className="button secondary small"
            onClick={handleExportCsv}
            disabled={total === 0 || isExporting}
            title={
              total === 0
                ? "No logs match current filters to export"
                : `Export all ${total} matching events to CSV`
            }
          >
            {isExporting ? (
              <>
                <RefreshCw size={15} style={{ animation: "spin 1s linear infinite" }} />
                <span>{exportProgress || "Exporting..."}</span>
              </>
            ) : (
              <>
                <Download size={15} />
                <span>Export CSV</span>
              </>
            )}
          </button>
          {exportError && (
            <span
              role="alert"
              style={{
                fontSize: "0.75rem",
                color: "#dc2626",
                marginTop: "4px",
              }}
            >
              {exportError}
            </span>
          )}
        </div>
      </div>

      <div className="admin-stats four">
        <StatCard
          label="Total events"
          value={totalEvents}
          icon={FileText}
          note="All recorded audit events"
        />
        <StatCard
          label="Successful actions"
          value={successCount}
          icon={CheckCircle}
          tone="green"
          note="Actions completed successfully"
        />
        <StatCard
          label="Failed attempts"
          value={failureCount}
          icon={AlertCircle}
          tone="red"
          note="Recorded in Security Events table"
        />
        <StatCard
          label="Warnings"
          value={warningCount}
          icon={Clock}
          tone="amber"
          note="Security anomalies requiring review"
        />
      </div>

      <ChartCard
        title="Filter audit events"
        subtitle="Search and filter the complete audit trail"
      >
        <div className="admin-audit-search">
          <SearchBar
            value={search}
            onChange={(v) => {
              setSearch(v);
            }}
            placeholder="Search by log ID, actor, action or resource…"
          />
        </div>
        <div className="admin-filters">
          <FilterDropdown
            label="Actor"
            value={actor}
            options={[
              { value: "all", label: "All actors" },
              ...actors.map((a) => ({ value: a, label: a })),
            ]}
            onChange={(v) => {
              setActor(v);
              setPage(1);
            }}
          />
          <FilterDropdown
            label="Action type"
            value={action}
            options={[
              { value: "all", label: "All actions" },
              ...actions.map((a) => ({ value: a, label: a })),
            ]}
            onChange={(v) => {
              setAction(v);
              setPage(1);
            }}
          />
          <FilterDropdown
            label="Outcome"
            value={outcome}
            options={[
              { value: "all", label: "All outcomes" },
              { value: "Success", label: "Success" },
              { value: "Failure", label: "Failure" },
              { value: "Warning", label: "Warning" },
            ]}
            onChange={(v) => {
              setOutcome(v);
              setPage(1);
            }}
          />
          <div />
        </div>
        <div className="admin-filter-caption">
          <span>
            {total} event{total !== 1 ? "s" : ""} match current filters
          </span>
          <button className="text-link" onClick={resetFilters}>
            <Filter size={12} /> Reset filters
          </button>
        </div>
      </ChartCard>

      <ChartCard
        title="Audit trail"
        subtitle="All workspace access events, sorted newest first"
      >
        {logsLoading ? (
          <LoadingState />
        ) : logsError ? (
          <ErrorState message={logsError} retry={loadAuditLogs} />
        ) : logs.length === 0 ? (
          <EmptyState
            title="No matching events"
            message="Try adjusting your search or filter options."
            onReset={resetFilters}
          />
        ) : (
          <>
            <DataTable
              label="Audit log entries"
              headings={[
                "Log ID",
                "Actor",
                "Action",
                "Resource",
                "Outcome",
                "IP Address",
                "Timestamp",
              ]}
            >
              {logs.map((log) => {
                const Icon = ACTION_ICONS[log.action] || Shield;
                const outcomeClass =
                  log.outcome === "Success"
                    ? "status-completed"
                    : log.outcome === "Failure"
                      ? "risk-critical"
                      : "risk-medium";
                return (
                  <tr key={log.id}>
                    <td>
                      <strong>{log.id}</strong>
                    </td>
                    <td>
                      <div className="admin-audit-actor">
                        <span className="admin-person-avatar admin-audit-avatar">
                          {log.actor
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                        <div>
                          <strong>{log.actor}</strong>
                          <small>{log.actorRole}</small>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="admin-audit-action">
                        <Icon size={13} />
                        {log.action}
                      </div>
                    </td>
                    <td>
                      <strong>{log.resource}</strong>
                      <small>{log.resourceId}</small>
                    </td>
                    <td>
                      <span className={`admin-badge ${outcomeClass}`}>
                        {log.outcome}
                      </span>
                    </td>
                    <td className="admin-nowrap">
                      <code className="admin-ip">{log.ipAddress}</code>
                    </td>
                    <td className="admin-nowrap">
                      {localDate(log.timestamp, true)} IST
                    </td>
                  </tr>
                );
              })}
            </DataTable>
            <div className="admin-directory-footer">
              <Pagination
                page={page}
                size={PAGE_SIZE}
                total={total}
                onChange={setPage}
              />
            </div>
          </>
        )}
      </ChartCard>
    </>
  );
}
