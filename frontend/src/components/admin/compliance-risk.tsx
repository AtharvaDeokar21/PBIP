"use client";
import Link from "next/link";
import { useState, useMemo } from "react";
import {
  FileWarning,
  Scale,
  RefreshCw,
  CalendarDays,
  ArrowUpRight,
  ShieldAlert,
  CheckCircle,
  AlertTriangle,
  Users,
  Filter,
  TrendingUp,
} from "lucide-react";
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

type ComplianceAlert = {
  id: string;
  customerId: string;
  customerName: string;
  type: string;
  category: "KYC" | "AML" | "Reporting" | "Documentation" | "Transaction";
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Open" | "In review" | "Resolved";
  dueDate: string;
  raisedAt: string;
  description: string;
  assignedTo: string;
};

function generateComplianceAlerts(
  customers: { id: string; name: string }[],
  asOf: string,
): ComplianceAlert[] {
  return [
    {
      id: "CA-1088",
      customerId: "C1011",
      customerName: "Arjun Singh",
      type: "Customer review overdue",
      category: "KYC",
      severity: "High",
      status: "Open",
      dueDate: "2026-10-10",
      raisedAt: `${asOf}T08:56:00+05:30`,
      description: "Periodic customer review is 15 days past the due date. Customer documents must be re-verified.",
      assignedTo: "Ravi Kumar",
    },
    {
      id: "CA-1087",
      customerId: "C1003",
      customerName: "Rohan Kapoor",
      type: "Account documentation review",
      category: "Documentation",
      severity: "Medium",
      status: "Open",
      dueDate: "2026-10-12",
      raisedAt: `2026-10-04T14:08:00+05:30`,
      description: "Supporting documents for the current account are outdated. Updated proof of address required.",
      assignedTo: "Ravi Kumar",
    },
    {
      id: "CA-1086",
      customerId: "C1005",
      customerName: "Kabir Joshi",
      type: "Suspicious transaction pattern",
      category: "AML",
      severity: "High",
      status: "In review",
      dueDate: "2026-10-08",
      raisedAt: `2026-10-03T11:00:00+05:30`,
      description: "Multiple high-value transactions to an unregistered offshore entity detected in Q3.",
      assignedTo: "Ravi Kumar",
    },
    {
      id: "CA-1085",
      customerId: "C1009",
      customerName: "Vivaan Desai",
      type: "Threshold reporting required",
      category: "Reporting",
      severity: "Medium",
      status: "In review",
      dueDate: "2026-10-15",
      raisedAt: `2026-10-02T09:30:00+05:30`,
      description: "Cash transaction report must be filed for transactions above ₹10,00,000 in October.",
      assignedTo: "Ravi Kumar",
    },
    {
      id: "CA-1084",
      customerId: "C1002",
      customerName: "Diya Mehta",
      type: "AML watch list match",
      category: "AML",
      severity: "Critical",
      status: "In review",
      dueDate: "2026-10-06",
      raisedAt: `2026-10-01T16:00:00+05:30`,
      description: "Customer name appears in an updated sanctions cross-reference. Escalation mandated within 48 hours.",
      assignedTo: "Ravi Kumar",
    },
    {
      id: "CA-1083",
      customerId: "C1001",
      customerName: "Aarav Shah",
      type: "Income declaration mismatch",
      category: "KYC",
      severity: "Low",
      status: "Resolved",
      dueDate: "2026-09-30",
      raisedAt: `2026-09-25T10:00:00+05:30`,
      description: "Declared income inconsistent with transaction volume. Customer submitted revised income proof.",
      assignedTo: "Ravi Kumar",
    },
    {
      id: "CA-1082",
      customerId: "C1007",
      customerName: "Ishaan Patel",
      type: "Transaction velocity breach",
      category: "Transaction",
      severity: "Medium",
      status: "Resolved",
      dueDate: "2026-09-28",
      raisedAt: `2026-09-22T13:00:00+05:30`,
      description: "Daily transaction count exceeded permissible threshold. Account temporarily rate-limited.",
      assignedTo: "Ravi Kumar",
    },
  ];
}

const CATEGORY_LABELS: Record<string, string> = {
  KYC: "Know Your Customer",
  AML: "Anti-Money Laundering",
  Reporting: "Regulatory Reporting",
  Documentation: "Documentation",
  Transaction: "Transaction Monitoring",
};

const PAGE_SIZE = 10;

export default function ComplianceRisk() {
  const { data, loading, error, refresh } = useAdminData();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);

  const complianceAlerts = useMemo(
    () =>
      data
        ? generateComplianceAlerts(
            data.customers.map((c) => ({ id: c.id, name: c.name })),
            data.asOf,
          )
        : [],
    [data],
  );

  const filtered = useMemo(
    () =>
      complianceAlerts.filter(
        (alert) =>
          (category === "all" || alert.category === category) &&
          (severity === "all" || alert.severity === severity) &&
          (status === "all" || alert.status === status) &&
          (search === "" ||
            alert.id.toLowerCase().includes(search.toLowerCase()) ||
            alert.customerName.toLowerCase().includes(search.toLowerCase()) ||
            alert.type.toLowerCase().includes(search.toLowerCase())),
      ),
    [complianceAlerts, category, severity, status, search],
  );

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;

  const openCount = complianceAlerts.filter((a) => a.status === "Open").length;
  const criticalCount = complianceAlerts.filter((a) => a.severity === "Critical").length;
  const resolvedCount = complianceAlerts.filter((a) => a.status === "Resolved").length;
  const highRiskCustomers = data.customers.filter((c) => c.risk === "High" || c.risk === "Critical").length;

  const categoryRows = ["KYC", "AML", "Reporting", "Documentation", "Transaction"].map(
    (label) => ({
      label: CATEGORY_LABELS[label] || label,
      value: complianceAlerts.filter((a) => a.category === label).length,
    }),
  );

  const riskRows = ["Low", "Medium", "High", "Critical"].map((label) => ({
    label,
    value: data.customers.filter((c) => c.risk === label).length,
  }));

  function resetFilters() {
    setSearch("");
    setCategory("all");
    setSeverity("all");
    setStatus("all");
    setPage(1);
  }

  return (
    <>
      <PageTitle
        title="Compliance & Risk"
        subtitle="Regulatory compliance alerts, risk distribution and customer risk profiles."
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
              {openCount} open alerts · {highRiskCustomers} high-risk customers · {resolvedCount} resolved this period.
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
            Risk levels are derived from transaction patterns, profile data and alert history.
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
          headings={["Customer", "Segment", "Risk score", "Risk level", "Open alerts", "Action"]}
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
                        {c.name.split(" ").map((n) => n[0]).join("")}
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
                      <span className="admin-risk-score-pill">{c.riskScore}</span>
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
            onChange={(v) => { setSearch(v); setPage(1); }}
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
            onChange={(v) => { setCategory(v); setPage(1); }}
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
            onChange={(v) => { setSeverity(v); setPage(1); }}
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
            onChange={(v) => { setStatus(v); setPage(1); }}
          />
          <div />
        </div>
        <div className="admin-filter-caption">
          <span>
            {filtered.length} alert{filtered.length !== 1 ? "s" : ""} match current filters
          </span>
          <button className="text-link" onClick={resetFilters}>
            <Filter size={12} /> Reset filters
          </button>
        </div>

        {paginated.length === 0 ? (
          <EmptyState
            title="No matching compliance alerts"
            message="Try adjusting the search or filter options."
            onReset={resetFilters}
          />
        ) : (
          <>
            <DataTable
              label="Compliance alert register"
              headings={["Alert ID", "Customer", "Type", "Category", "Severity", "Status", "Due date", "Raised"]}
            >
              {paginated.map((alert) => {
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
                      {isPastDue && <AlertTriangle size={11} />}{" "}
                      {alert.dueDate}
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
