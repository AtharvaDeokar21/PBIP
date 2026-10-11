"use client";
import Link from "next/link";
import { useState, useMemo } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  CalendarDays,
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

type SecurityEvent = {
  id: string;
  customerId: string;
  customerName: string;
  eventType: string;
  channel: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Open" | "In review" | "Resolved";
  detectedAt: string;
  description: string;
  location: string;
  device: string;
};

const EVENT_TYPE_ICONS: Record<string, LucideIcon> = {
  "Unusual login": Lock,
  "Multiple failures": Lock,
  "New device": Smartphone,
  "Suspicious transfer": CreditCard,
  "Geo anomaly": Wifi,
  "Card misuse": CreditCard,
  "API abuse": Activity,
};

function generateSecurityEvents(
  customers: { id: string; name: string; risk: string }[],
  asOf: string,
): SecurityEvent[] {
  const events: SecurityEvent[] = [
    {
      id: "SE-4021",
      customerId: "C1002",
      customerName: "Diya Mehta",
      eventType: "Unusual login",
      channel: "Mobile app",
      severity: "Critical",
      status: "Open",
      detectedAt: `${asOf}T09:42:00+05:30`,
      description: "Login from unrecognised IP in a foreign country.",
      location: "Frankfurt, DE",
      device: "iPhone 14",
    },
    {
      id: "SE-4020",
      customerId: "C1005",
      customerName: "Kabir Joshi",
      eventType: "Suspicious transfer",
      channel: "Net banking",
      severity: "High",
      status: "In review",
      detectedAt: `${asOf}T08:18:00+05:30`,
      description:
        "Transfer to an unregistered beneficiary exceeding daily limit.",
      location: "Mumbai, IN",
      device: "Chrome / Windows",
    },
    {
      id: "SE-4019",
      customerId: "C1007",
      customerName: "Ishaan Patel",
      eventType: "Multiple failures",
      channel: "Net banking",
      severity: "High",
      status: "In review",
      detectedAt: `${asOf}T07:20:00+05:30`,
      description:
        "Seven consecutive login failures detected within 4 minutes.",
      location: "Bengaluru, IN",
      device: "Firefox / Linux",
    },
    {
      id: "SE-4018",
      customerId: "C1011",
      customerName: "Arjun Singh",
      eventType: "New device",
      channel: "Mobile app",
      severity: "Medium",
      status: "Open",
      detectedAt: `2026-10-04T18:30:00+05:30`,
      description: "First-time login from an unregistered Android device.",
      location: "Delhi, IN",
      device: "Samsung Galaxy S23",
    },
    {
      id: "SE-4017",
      customerId: "C1003",
      customerName: "Rohan Kapoor",
      eventType: "Geo anomaly",
      channel: "ATM",
      severity: "Medium",
      status: "Open",
      detectedAt: `2026-10-04T15:12:00+05:30`,
      description: "Withdrawal in Chennai 30 minutes after a Pune transaction.",
      location: "Chennai, IN",
      device: "ATM Terminal",
    },
    {
      id: "SE-4016",
      customerId: "C1009",
      customerName: "Vivaan Desai",
      eventType: "API abuse",
      channel: "API",
      severity: "Medium",
      status: "In review",
      detectedAt: `2026-10-04T11:00:00+05:30`,
      description: "Rate limit exceeded on transaction history endpoint.",
      location: "Pune, IN",
      device: "API Client",
    },
    {
      id: "SE-4015",
      customerId: "C1001",
      customerName: "Aarav Shah",
      eventType: "New device",
      channel: "Mobile app",
      severity: "Low",
      status: "Resolved",
      detectedAt: `2026-10-03T14:00:00+05:30`,
      description: "Login from a new iPad recognised after OTP verification.",
      location: "Ahmedabad, IN",
      device: "iPad Pro",
    },
  ];
  return events;
}

const PAGE_SIZE = 10;

export default function FraudSecurityMonitoring() {
  const { data, loading, error, refresh } = useAdminData();
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");
  const [channel, setChannel] = useState("all");
  const [page, setPage] = useState(1);

  const events = useMemo(
    () =>
      data
        ? generateSecurityEvents(
            data.customers.map((c) => ({
              id: c.id,
              name: c.name,
              risk: c.risk ?? "Low",
            })),
            data.asOf,
          )
        : [],
    [data],
  );

  const fraudAlerts = useMemo(
    () => (data ? activeAlerts(data).filter((a) => a.domain === "Fraud") : []),
    [data],
  );

  const filtered = useMemo(
    () =>
      events.filter(
        (ev) =>
          (severity === "all" || ev.severity === severity) &&
          (status === "all" || ev.status === status) &&
          (channel === "all" || ev.channel === channel) &&
          (search === "" ||
            ev.id.toLowerCase().includes(search.toLowerCase()) ||
            ev.customerName.toLowerCase().includes(search.toLowerCase()) ||
            ev.eventType.toLowerCase().includes(search.toLowerCase()) ||
            ev.description.toLowerCase().includes(search.toLowerCase())),
      ),
    [events, severity, status, channel, search],
  );

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;

  const criticalCount = events.filter((e) => e.severity === "Critical").length;
  const openCount = events.filter((e) => e.status === "Open").length;
  const resolvedCount = events.filter((e) => e.status === "Resolved").length;

  const severityRows = ["Critical", "High", "Medium", "Low"].map((label) => ({
    label,
    value: events.filter((e) => e.severity === label).length,
  }));

  const channelRows = ["Mobile app", "Net banking", "ATM", "API"].map(
    (label) => ({
      label,
      value: events.filter((e) => e.channel === label).length,
    }),
  );

  function resetFilters() {
    setSearch("");
    setSeverity("all");
    setStatus("all");
    setChannel("all");
    setPage(1);
  }

  return (
    <>
      <PageTitle
        title="Fraud & Security Monitoring"
        subtitle="Real-time security events, fraud signals and anomaly detection across all channels."
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
              {openCount} open events · {fraudAlerts.length} active fraud alerts
              · monitoring live across all channels.
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
          value={events.length}
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
          label="Open events"
          value={openCount}
          icon={Eye}
          tone="amber"
          note="Events pending action or assignment"
        />
        <StatCard
          label="Resolved"
          value={resolvedCount}
          icon={ShieldCheck}
          tone="green"
          note="Events closed in this period"
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
              setPage(1);
            }}
            placeholder="Search by event ID, customer, type or description…"
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
              { value: "Open", label: "Open" },
              { value: "In review", label: "In review" },
              { value: "Resolved", label: "Resolved" },
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
              { value: "Mobile app", label: "Mobile app" },
              { value: "Net banking", label: "Net banking" },
              { value: "ATM", label: "ATM" },
              { value: "API", label: "API" },
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
            {filtered.length} event{filtered.length !== 1 ? "s" : ""} match
            current filters
          </span>
          <button className="text-link" onClick={resetFilters}>
            <Filter size={12} /> Reset filters
          </button>
        </div>
        {paginated.length === 0 ? (
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
                "Customer",
                "Type",
                "Channel",
                "Severity",
                "Status",
                "Location",
                "Detected",
              ]}
            >
              {paginated.map((ev) => {
                const Icon = EVENT_TYPE_ICONS[ev.eventType] || ShieldAlert;
                return (
                  <tr key={ev.id}>
                    <td>
                      <strong>{ev.id}</strong>
                    </td>
                    <td>
                      <Link
                        className="admin-table-link"
                        href={`/admin/customers/${ev.customerId}`}
                      >
                        {ev.customerName} <ArrowUpRight size={12} />
                      </Link>
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
