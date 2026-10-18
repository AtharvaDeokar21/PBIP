"use client";
import Link from "next/link";
import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  ArrowUpRight,
  Filter,
  Eye,
  Lock,
  Wifi,
  CreditCard,
  Smartphone,
  Activity,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useAdminData } from "./use-admin-data";
import {
  PageTitle,
  AdminHeaderDate,
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
  HorizontalBars,
  Pagination,
} from "./ui";
import { activeAlerts, localDate } from "@/lib/admin/metrics";
import type { SecurityEventItem, SecuritySummary } from "@/lib/admin/types";
import { fetchSecurityEvents } from "@/lib/admin/api";

const EVENT_TYPE_ICONS: Record<string, LucideIcon> = {
  "Login successful": Lock,
  "Login failed": Lock,
  "High value transfer": CreditCard,
  "Unusual login": Lock,
  "Multiple failures": Lock,
  "New device": Smartphone,
  "Suspicious transfer": CreditCard,
  "Geo anomaly": Wifi,
  "Card misuse": CreditCard,
  "API abuse": Activity,
};

const PAGE_SIZE = 10;

export default function FraudSecurityMonitoring() {
  const { data, loading: adminLoading, error: adminError, refresh: refreshAdmin } =
    useAdminData();

  const [events, setEvents] = useState<SecurityEventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [eventsError, setEventsError] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");
  const [channel, setChannel] = useState("all");
  const [page, setPage] = useState(1);

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
  const loadSecurityEvents = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;
    setEventsLoading(true);
    setEventsError("");

    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    });

    if (severity !== "all") params.set("severity", severity);
    if (status !== "all") params.set("status", status);
    if (channel !== "all") params.set("channel", channel);
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());

    try {
      const res = await fetchSecurityEvents(params);
      if (currentRequestId === requestIdRef.current) {
        setEvents(res.items);
        setTotal(res.total);
        setSummary(res.summary);
      }
    } catch (err: unknown) {
      if (currentRequestId === requestIdRef.current) {
        setEventsError(
          err instanceof Error
            ? err.message
            : "Failed to load security events from server.",
        );
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setEventsLoading(false);
      }
    }
  }, [page, severity, status, channel, debouncedSearch]);

  useEffect(() => {
    loadSecurityEvents();
  }, [loadSecurityEvents]);

  const refreshAll = useCallback(() => {
    refreshAdmin();
    loadSecurityEvents();
  }, [refreshAdmin, loadSecurityEvents]);

  const fraudAlerts = useMemo(
    () => (data ? activeAlerts(data).filter((a) => a.domain === "Fraud") : []),
    [data],
  );

  function resetFilters() {
    setSearch("");
    setDebouncedSearch("");
    setSeverity("all");
    setStatus("all");
    setChannel("all");
    setPage(1);
  }

  if (adminLoading) return <LoadingState />;
  if (adminError || !data) {
    return <ErrorState message={adminError || "Unable to load dashboard data."} retry={refreshAll} />;
  }

  const criticalCount = summary?.criticalCount ?? 0;
  const reviewCount = summary?.requiresReviewCount ?? summary?.openCount ?? 0;
  const loggedCount = summary?.loggedCount ?? summary?.resolvedCount ?? 0;
  const totalEvents = summary?.totalEvents ?? total;

  const severityRows = ["Critical", "High", "Medium", "Low"].map((label) => ({
    label,
    value: summary?.severityCounts?.[label] ?? 0,
  }));

  const channelRows = ["Mobile app", "Net banking", "ATM", "API"].map((label) => ({
    label,
    value: summary?.channelCounts?.[label] ?? 0,
  }));

  return (
    <>
      <PageTitle
        title="Fraud & Security Monitoring"
        subtitle="Real-time security events, fraud signals and anomaly detection across all channels."
        action={
          <div className="admin-title-actions">
            <AdminHeaderDate />
            <button className="button secondary small" onClick={refreshAll}>
              <RefreshCw size={15} /> Refresh
            </button>
          </div>
        }
      />

      <div className="admin-overview-banner admin-fraud-banner">
        <div>
          <span className="admin-banner-icon admin-banner-icon-red">
            <ShieldAlert size={28} />
          </span>
          <div>
            <h2>
              {criticalCount > 0
                ? `${criticalCount} critical alert${criticalCount > 1 ? "s" : ""} require immediate attention.`
                : "All critical threats are under control."}
            </h2>
            <p>
              {reviewCount} event{reviewCount !== 1 ? "s" : ""} requiring review · {fraudAlerts.length} active fraud alert{fraudAlerts.length !== 1 ? "s" : ""} · monitoring live across all channels.
            </p>
          </div>
        </div>
        <Link href="/admin/investigations">
          Open investigations <ArrowUpRight size={17} />
        </Link>
      </div>

      <div className="admin-stats four">
        <StatCard
          label="Total security events"
          value={totalEvents}
          icon={ShieldAlert}
          note="All events in the monitoring window"
        />
        <StatCard
          label="Critical events"
          value={criticalCount}
          icon={AlertTriangle}
          tone="red"
          note="Events requiring immediate response"
        />
        <StatCard
          label="Requires review"
          value={reviewCount}
          icon={Eye}
          tone="amber"
          note="Events flagged for review (e.g. failed logins)"
        />
        <StatCard
          label="Logged"
          value={loggedCount}
          icon={ShieldCheck}
          tone="green"
          note="Standard access events logged"
        />
      </div>

      <div className="admin-grid two">
        <ChartCard
          title="Events by severity"
          subtitle="Distribution of security events by risk level"
        >
          <HorizontalBars rows={severityRows} />
        </ChartCard>
        <ChartCard
          title="Events by channel"
          subtitle="Security events grouped by originating channel"
        >
          <HorizontalBars rows={channelRows} />
        </ChartCard>
      </div>

      <ChartCard
        title="Active fraud alerts"
        subtitle="Unresolved fraud signals from the alert system"
        action={
          <Link className="text-link" href="/admin/investigations">
            View investigations <ArrowUpRight size={15} />
          </Link>
        }
      >
        {fraudAlerts.length === 0 ? (
          <EmptyState
            title="No active fraud alerts"
            message="All alerts have been resolved."
          />
        ) : (
          <DataTable
            label="Active fraud alerts"
            headings={[
              "Alert ID",
              "Customer",
              "Type",
              "Severity",
              "Status",
              "Detected",
            ]}
          >
            {fraudAlerts.map((alert) => {
              const customer = data.customers.find(
                (c) => c.id === alert.customerId,
              );
              return (
                <tr key={alert.id}>
                  <td>
                    <strong>{alert.id}</strong>
                    <small>{alert.domain}</small>
                  </td>
                  <td>
                    <Link
                      className="admin-table-link"
                      href={`/admin/customers/${alert.customerId}`}
                    >
                      {customer?.name} <ArrowUpRight size={12} />
                    </Link>
                  </td>
                  <td>{alert.type}</td>
                  <td>
                    <RiskBadge risk={alert.severity} />
                  </td>
                  <td>
                    <StatusBadge status={alert.status} />
                  </td>
                  <td className="admin-nowrap">
                    {localDate(alert.date, true)} IST
                  </td>
                </tr>
              );
            })}
          </DataTable>
        )}
      </ChartCard>

      <ChartCard
        title="Security event log"
        subtitle="All detected anomalies and security incidents, most recent first"
      >
        <div className="admin-audit-search">
          <SearchBar
            value={search}
            onChange={(v) => {
              setSearch(v);
            }}
            placeholder="Search by event ID, IP, user, type or description…"
          />
        </div>
        <div className="admin-filters">
          <FilterDropdown
            label="Severity"
            value={severity}
            options={[
              { value: "all", label: "All severities" },
              { value: "Critical", label: "Critical" },
              { value: "High", label: "High" },
              { value: "Medium", label: "Medium" },
              { value: "Low", label: "Low" },
            ]}
            onChange={(v) => {
              setSeverity(v);
              setPage(1);
            }}
          />
          <FilterDropdown
            label="Status"
            value={status}
            options={[
              { value: "all", label: "All statuses" },
              { value: "Requires review", label: "Requires review" },
              { value: "Logged", label: "Logged" },
            ]}
            onChange={(v) => {
              setStatus(v);
              setPage(1);
            }}
          />
          <FilterDropdown
            label="Channel"
            value={channel}
            options={[
              { value: "all", label: "All channels" },
              { value: "Net banking", label: "Net banking" },
              { value: "API", label: "API" },
              { value: "Mobile app", label: "Mobile app" },
              { value: "ATM", label: "ATM" },
            ]}
            onChange={(v) => {
              setChannel(v);
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
        {eventsLoading ? (
          <LoadingState />
        ) : eventsError ? (
          <ErrorState message={eventsError} retry={loadSecurityEvents} />
        ) : events.length === 0 ? (
          <EmptyState
            title="No matching events"
            message="Try adjusting the search or filter options."
            onReset={resetFilters}
          />
        ) : (
          <>
            <DataTable
              label="Security events"
              headings={[
                "Event ID",
                "Customer / User",
                "Type",
                "Channel",
                "Severity",
                "Status",
                "Location",
                "Detected",
              ]}
            >
              {events.map((ev) => {
                const Icon = EVENT_TYPE_ICONS[ev.eventType] || ShieldAlert;
                return (
                  <tr key={ev.id}>
                    <td>
                      <strong>{ev.id}</strong>
                    </td>
                    <td>
                      {ev.customerId ? (
                        <Link
                          className="admin-table-link"
                          href={`/admin/customers/${ev.customerId}`}
                        >
                          {ev.customerName} <ArrowUpRight size={12} />
                        </Link>
                      ) : (
                        <span style={{ color: "var(--admin-muted)", fontSize: "10px" }}>
                          {ev.customerName || "System / Internal"}
                        </span>
                      )}
                    </td>
                    <td>
                      <div className="admin-audit-action">
                        <Icon size={13} />
                        <div>
                          <strong>{ev.eventType}</strong>
                          <small>{ev.description}</small>
                        </div>
                      </div>
                    </td>
                    <td>{ev.channel}</td>
                    <td>
                      <RiskBadge risk={ev.severity} />
                    </td>
                    <td>
                      <StatusBadge status={ev.status} />
                    </td>
                    <td className="admin-nowrap">{ev.location}</td>
                    <td className="admin-nowrap">
                      {localDate(ev.detectedAt, true)} IST
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
