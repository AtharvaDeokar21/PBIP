"use client";
import Link from "next/link";
import { useState, useMemo, useEffect, useCallback, useRef } from "react";
import {
  FileWarning,
  Scale,
  RefreshCw,
  ArrowUpRight,
  ShieldAlert,
  CheckCircle,
  AlertTriangle,
  Users,
  Filter,
} from "lucide-react";
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
import type {
  ComplianceAlertItem,
  ComplianceCategory,
  ComplianceSummary,
} from "@/lib/admin/types";
import { fetchComplianceAlerts } from "@/lib/admin/api";

const CATEGORY_LABELS: Record<string, string> = {
  KYC: "Know Your Customer",
  AML: "Anti-Money Laundering",
  Reporting: "Regulatory Reporting",
  Documentation: "Documentation",
  Transaction: "Transaction Monitoring",
};

const PAGE_SIZE = 10;

export default function ComplianceRisk() {
  const { data, loading: adminLoading, error: adminError, refresh: refreshAdmin } = useAdminData();
  const [alerts, setAlerts] = useState<ComplianceAlertItem[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");
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
  const loadComplianceAlerts = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;
    setAlertsLoading(true);
    setAlertsError("");

    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    });

    if (category !== "all") params.set("category", category);
    if (severity !== "all") params.set("severity", severity);
    if (status !== "all") params.set("status", status);
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());

    const asOf = data?.asOf?.trim();
    if (asOf && /^\d{4}-\d{2}-\d{2}$/.test(asOf)) {
      params.set("as_of", asOf);
    }

    try {
      const res = await fetchComplianceAlerts(params);
      if (currentRequestId === requestIdRef.current) {
        setAlerts(res.items);
        setTotal(res.total);
        setSummary(res.summary);
      }
    } catch (err: unknown) {
      if (currentRequestId === requestIdRef.current) {
        setAlertsError(
          err instanceof Error
            ? err.message
            : "Failed to load compliance alerts from server.",
        );
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setAlertsLoading(false);
      }
    }
  }, [page, category, severity, status, debouncedSearch, data?.asOf]);

  useEffect(() => {
    loadComplianceAlerts();
  }, [loadComplianceAlerts]);

  const refreshAll = useCallback(() => {
    refreshAdmin();
    loadComplianceAlerts();
  }, [refreshAdmin, loadComplianceAlerts]);

  function resetFilters() {
    setSearch("");
    setDebouncedSearch("");
    setCategory("all");
    setSeverity("all");
    setStatus("all");
    setPage(1);
  }

  if (adminLoading) return <LoadingState />;
  if (adminError || !data) return <ErrorState message={adminError} retry={refreshAll} />;

  const openCount = summary?.openCount ?? 0;
  const criticalCount = summary?.criticalCount ?? 0;
  const resolvedCount = summary?.resolvedCount ?? 0;
  const highRiskCustomers = data.customers.filter(
    (c) => c.risk === "High" || c.risk === "Critical",
  ).length;

  const categoryRows = [
    "KYC",
    "AML",
    "Reporting",
    "Documentation",
    "Transaction",
  ].map((label) => ({
    label: CATEGORY_LABELS[label] || label,
    value: summary?.categoryCounts?.[label] ?? 0,
  }));

  const riskRows = ["Low", "Medium", "High", "Critical"].map((label) => ({
    label,
    value: data.customers.filter((c) => c.risk === label).length,
  }));

  return (
    <>
      <PageTitle
        title="Compliance & Risk"
        subtitle="Regulatory compliance alerts, risk distribution and customer risk profiles."
        action={
          <div className="admin-title-actions">
            <AdminHeaderDate snapshotDate={data.asOf} />
            <button className="button secondary small" onClick={refreshAll}>
              <RefreshCw size={15} /> Refresh
            </button>
          </div>
        }
      />

      <div className="admin-overview-banner admin-compliance-banner">
        <div>
          <span className="admin-banner-icon admin-banner-icon-amber">
            <Scale size={28} />
          </span>
          <div>
            <h2>
              {criticalCount > 0
                ? `${criticalCount} critical compliance matter${criticalCount > 1 ? "s" : ""} require immediate action.`
                : "No critical compliance exceptions at this time."}
            </h2>
            <p>
              {openCount} open alerts · {highRiskCustomers} high-risk customers
              · {resolvedCount} resolved this period.
            </p>
          </div>
        </div>
        <Link href="/admin/audit-logs">
          View audit logs <ArrowUpRight size={17} />
        </Link>
      </div>

      <div className="admin-stats four">
        <StatCard
          label="Open compliance alerts"
          value={openCount}
          icon={FileWarning}
          tone="amber"
          note="Alerts awaiting action or review"
        />
        <StatCard
          label="Critical exceptions"
          value={criticalCount}
          icon={AlertTriangle}
          tone="red"
          note="Highest priority compliance matters"
        />
        <StatCard
          label="High-risk customers"
          value={highRiskCustomers}
          icon={Users}
          tone="amber"
          note="Customers flagged as high or critical risk"
          href="/admin/customers?risk=High"
        />
        <StatCard
          label="Resolved this period"
          value={resolvedCount}
          icon={CheckCircle}
          tone="green"
          note="Compliance alerts closed"
        />
      </div>

      <div className="admin-grid two">
        <ChartCard
          title="Alerts by regulatory category"
          subtitle="Distribution of compliance exceptions by category"
        >
          <HorizontalBars rows={categoryRows} />
        </ChartCard>
        <ChartCard
          title="Customer risk distribution"
          subtitle="Overall risk profile across the customer base"
        >
          <HorizontalBars rows={riskRows} />
          <p className="admin-chart-caption">
            Risk levels are derived from transaction patterns, profile data and
            alert history.
          </p>
        </ChartCard>
      </div>

      <ChartCard
        title="High-risk customer overview"
        subtitle="Customers with elevated risk scores requiring compliance attention"
        action={
          <Link className="text-link" href="/admin/customers?risk=High">
            View all customers <ArrowUpRight size={15} />
          </Link>
        }
      >
        <DataTable
          label="High-risk customers"
          headings={[
            "Customer",
            "Segment",
            "Risk score",
            "Risk level",
            "Open alerts",
            "Action",
          ]}
        >
          {data.customers
            .filter((c) => c.risk === "High" || c.risk === "Critical")
            .map((c) => {
              const customerAlerts = activeAlerts(data, c.id);
              return (
                <tr key={c.id}>
                  <td>
                    <div className="admin-customer-cell">
                      <span className="admin-customer-avatar">
                        {c.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </span>
                      <div>
                        <strong>{c.name}</strong>
                        <small>{c.id}</small>
                      </div>
                    </div>
                  </td>
                  <td>{c.segment}</td>
                  <td>
                    <div className="admin-risk-bar-cell">
                      <span className="admin-risk-score-pill">
                        {c.riskScore}
                      </span>
                      <div className="admin-risk-mini-bar">
                        <span
                          style={{
                            width: `${c.riskScore}%`,
                            background:
                              c.riskScore >= 70
                                ? "#c45566"
                                : c.riskScore >= 40
                                  ? "#c7944d"
                                  : "#44856d",
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <RiskBadge risk={c.risk} />
                  </td>
                  <td>
                    <span
                      className={`admin-alert-count ${customerAlerts.length > 0 ? "has-alerts" : ""}`}
                    >
                      {customerAlerts.length}
                    </span>
                  </td>
                  <td>
                    <Link
                      className="admin-table-link"
                      href={`/admin/customers/${c.id}`}
                    >
                      View profile <ArrowUpRight size={12} />
                    </Link>
                  </td>
                </tr>
              );
            })}
        </DataTable>
      </ChartCard>

      <ChartCard
        title="Compliance alert register"
        subtitle="All active and resolved regulatory compliance exceptions"
      >
        <div className="admin-audit-search">
          <SearchBar
            value={search}
            onChange={(v) => {
              setSearch(v);
            }}
            placeholder="Search by alert ID, customer or type…"
          />
        </div>
        <div className="admin-filters">
          <FilterDropdown
            label="Category"
            value={category}
            options={[
              { value: "all", label: "All categories" },
              { value: "KYC", label: "KYC" },
              { value: "AML", label: "AML" },
              { value: "Reporting", label: "Reporting" },
              { value: "Documentation", label: "Documentation" },
              { value: "Transaction", label: "Transaction Monitoring" },
            ]}
            onChange={(v) => {
              setCategory(v);
              setPage(1);
            }}
          />
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
          <div />
        </div>
        <div className="admin-filter-caption">
          <span>
            {total} alert{total !== 1 ? "s" : ""} match current filters
          </span>
          <button className="text-link" onClick={resetFilters}>
            <Filter size={12} /> Reset filters
          </button>
        </div>

        {alertsLoading ? (
          <LoadingState />
        ) : alertsError ? (
          <ErrorState message={alertsError} retry={loadComplianceAlerts} />
        ) : alerts.length === 0 ? (
          <EmptyState
            title="No matching compliance alerts"
            message="Try adjusting the search or filter options."
            onReset={resetFilters}
          />
        ) : (
          <>
            <DataTable
              label="Compliance alert register"
              headings={[
                "Alert ID",
                "Customer",
                "Type",
                "Category",
                "Severity",
                "Status",
                "Due date",
                "Raised",
              ]}
            >
              {alerts.map((alert) => {
                const isPastDue =
                  alert.status !== "Resolved" && alert.dueDate < data.asOf;
                return (
                  <tr key={alert.id}>
                    <td>
                      <strong>{alert.id}</strong>
                    </td>
                    <td>
                      <Link
                        className="admin-table-link"
                        href={`/admin/customers/${alert.customerId}`}
                      >
                        {alert.customerName} <ArrowUpRight size={12} />
                      </Link>
                    </td>
                    <td>
                      <strong>{alert.type}</strong>
                      <small
                        className="admin-compliance-description"
                        title={alert.description}
                      >
                        {alert.description.length > 60
                          ? `${alert.description.slice(0, 60)}…`
                          : alert.description}
                      </small>
                    </td>
                    <td>
                      <span className="admin-badge">{alert.category}</span>
                    </td>
                    <td>
                      <RiskBadge risk={alert.severity} />
                    </td>
                    <td>
                      <StatusBadge status={alert.status} />
                    </td>
                    <td
                      className={`admin-nowrap ${isPastDue ? "admin-overdue" : ""}`}
                    >
                      {isPastDue && <AlertTriangle size={11} />} {alert.dueDate}
                    </td>
                    <td className="admin-nowrap">
                      {localDate(alert.raisedAt, true)} IST
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
