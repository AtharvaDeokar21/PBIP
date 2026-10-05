"use client";
import { useState, useMemo } from "react";
import {
  FileText,
  Shield,
  RefreshCw,
  CalendarDays,
  Download,
  Filter,
  User,
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
  ChartCard,
  DataTable,
  RiskBadge,
  StatusBadge,
  FilterDropdown,
  SearchBar,
  EmptyState,
  LoadingState,
  ErrorState,
  StatCard,
  Pagination,
} from "./ui";
import { localDate } from "@/lib/admin/metrics";

const ACTION_ICONS: Record<string, LucideIcon> = {
  Login: LogIn,
  Logout: LogOut,
  "Profile update": Edit,
  "Password change": Key,
  "Account view": Eye,
  "Transaction view": Eye,
  "Alert review": AlertCircle,
  "Alert resolved": CheckCircle,
};

type AuditEntry = {
  id: string;
  actor: string;
  actorRole: string;
  action: string;
  resource: string;
  resourceId: string;
  outcome: "Success" | "Failure" | "Warning";
  ipAddress: string;
  timestamp: string;
  customerId?: string;
};

function generateAuditLogs(asOf: string): AuditEntry[] {
  const actors = [
    { name: "Alex Shah", role: "Administrator" },
    { name: "Priya Iyer", role: "Fraud Analyst" },
    { name: "Ravi Kumar", role: "Compliance Officer" },
    { name: "Sneha Gupta", role: "Relationship Manager" },
    { name: "Amit Verma", role: "Fraud Analyst" },
  ];
  const actions = [
    { action: "Login", resource: "Auth", outcome: "Success" as const },
    { action: "Alert review", resource: "Fraud Alert", outcome: "Success" as const },
    { action: "Alert resolved", resource: "Fraud Alert", outcome: "Success" as const },
    { action: "Account view", resource: "Customer Account", outcome: "Success" as const },
    { action: "Transaction view", resource: "Transaction", outcome: "Success" as const },
    { action: "Profile update", resource: "Customer Profile", outcome: "Success" as const },
    { action: "Login", resource: "Auth", outcome: "Failure" as const },
    { action: "Password change", resource: "Auth", outcome: "Success" as const },
    { action: "Alert review", resource: "Compliance Alert", outcome: "Warning" as const },
    { action: "Logout", resource: "Auth", outcome: "Success" as const },
  ];
  const ips = [
    "192.168.1.42", "10.0.0.15", "172.16.0.88", "192.168.10.5", "10.1.2.34",
  ];
  const customerIds = ["C1001", "C1002", "C1003", "C1004", "C1005", "C1006"];
  const logs: AuditEntry[] = [];
  const base = new Date(`${asOf}T10:00:00+05:30`);
  for (let i = 0; i < 48; i++) {
    const actor = actors[i % actors.length];
    const act = actions[i % actions.length];
    const offset = i * 23 * 60 * 1000;
    const ts = new Date(base.getTime() - offset).toISOString();
    logs.push({
      id: `AL-${3100 + i}`,
      actor: actor.name,
      actorRole: actor.role,
      action: act.action,
      resource: act.resource,
      resourceId: act.resource === "Auth"
        ? `USER-${1001 + (i % 5)}`
        : act.resource.includes("Customer")
          ? customerIds[i % customerIds.length]
          : `FA-${2030 + i}`,
      outcome: act.outcome,
      ipAddress: ips[i % ips.length],
      timestamp: ts,
      customerId:
        act.resource !== "Auth" ? customerIds[i % customerIds.length] : undefined,
    });
  }
  return logs;
}

const PAGE_SIZE = 15;

export default function AuditLogs() {
  const { data, loading, error, refresh } = useAdminData();
  const [search, setSearch] = useState("");
  const [actor, setActor] = useState("all");
  const [action, setAction] = useState("all");
  const [outcome, setOutcome] = useState("all");
  const [page, setPage] = useState(1);

  const logs = useMemo(
    () => (data ? generateAuditLogs(data.asOf) : []),
    [data],
  );

  const filtered = useMemo(
    () =>
      logs.filter(
        (log) =>
          (actor === "all" || log.actor === actor) &&
          (action === "all" || log.action === action) &&
          (outcome === "all" || log.outcome === outcome) &&
          (search === "" ||
            log.id.toLowerCase().includes(search.toLowerCase()) ||
            log.actor.toLowerCase().includes(search.toLowerCase()) ||
            log.action.toLowerCase().includes(search.toLowerCase()) ||
            log.resource.toLowerCase().includes(search.toLowerCase())),
      ),
    [logs, actor, action, outcome, search],
  );

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;

  const actors = Array.from(new Set(logs.map((l) => l.actor)));
  const actions = Array.from(new Set(logs.map((l) => l.action)));

  const successCount = logs.filter((l) => l.outcome === "Success").length;
  const failureCount = logs.filter((l) => l.outcome === "Failure").length;
  const warningCount = logs.filter((l) => l.outcome === "Warning").length;

  function resetFilters() {
    setSearch("");
    setActor("all");
    setAction("all");
    setOutcome("all");
    setPage(1);
  }

  return (
    <>
      <PageTitle
        title="Audit Logs"
        subtitle="Complete record of all internal workspace actions, access events and system changes."
        action={
          <div className="admin-title-actions">
            <span className="admin-date">
              <CalendarDays size={16} />
              {localDate(data.asOf)}
            </span>
            <button className="button secondary small" onClick={refresh}>
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
              {logs.length} events recorded · {failureCount} failed attempts ·{" "}
              {warningCount} warnings requiring review.
            </p>
          </div>
        </div>
        <button className="button secondary small">
          <Download size={15} /> Export CSV
        </button>
      </div>

      <div className="admin-stats four">
        <StatCard
          label="Total events"
          value={logs.length}
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
          note="Actions that failed or were blocked"
        />
        <StatCard
          label="Warnings"
          value={warningCount}
          icon={Clock}
          tone="amber"
          note="Actions requiring review"
        />
      </div>

      <ChartCard
        title="Filter audit events"
        subtitle="Search and filter the complete audit trail"
      >
        <div className="admin-audit-search">
          <SearchBar
            value={search}
            onChange={(v) => { setSearch(v); setPage(1); }}
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
            onChange={(v) => { setActor(v); setPage(1); }}
          />
          <FilterDropdown
            label="Action type"
            value={action}
            options={[
              { value: "all", label: "All actions" },
              ...actions.map((a) => ({ value: a, label: a })),
            ]}
            onChange={(v) => { setAction(v); setPage(1); }}
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
            onChange={(v) => { setOutcome(v); setPage(1); }}
          />
          <div />
        </div>
        <div className="admin-filter-caption">
          <span>
            {filtered.length} event{filtered.length !== 1 ? "s" : ""} match
            current filters
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
        {paginated.length === 0 ? (
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
              {paginated.map((log) => {
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
                total={filtered.length}
                onChange={setPage}
              />
            </div>
          </>
        )}
      </ChartCard>
    </>
  );
}
