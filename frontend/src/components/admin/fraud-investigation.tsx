"use client";
import Link from "next/link";
import { useState, useMemo } from "react";
import {
  ScanSearch,
  ShieldAlert,
  RefreshCw,
  CalendarDays,
  ArrowUpRight,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  User,
  FileText,
  MessageSquare,
  ChevronDown,
  ChevronUp,
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
  Pagination,
} from "./ui";
import { activeAlerts, localDate } from "@/lib/admin/metrics";
import type { Risk } from "@/lib/admin/types";

type Investigation = {
  id: string;
  alertId: string;
  customerId: string;
  customerName: string;
  type: string;
  severity: Risk;
  status: "Open" | "In review" | "Escalated" | "Resolved" | "False positive";
  assignedTo: string;
  openedAt: string;
  updatedAt: string;
  notes: string[];
  riskScore: number;
  amount?: number;
};

function generateInvestigations(asOf: string): Investigation[] {
  return [
    {
      id: "INV-0041",
      alertId: "FA-2041",
      customerId: "C1002",
      customerName: "Diya Mehta",
      type: "Unusual transfer amount",
      severity: "Critical",
      status: "Open",
      assignedTo: "Priya Iyer",
      openedAt: `${asOf}T09:42:00+05:30`,
      updatedAt: `${asOf}T09:42:00+05:30`,
      notes: [
        "Alert auto-generated: transfer of ₹4,85,000 to unverified beneficiary.",
        "Customer has no prior history of transactions above ₹1,00,000.",
      ],
      riskScore: 91,
      amount: 485000,
    },
    {
      id: "INV-0040",
      alertId: "FA-2040",
      customerId: "C1005",
      customerName: "Kabir Joshi",
      type: "New sign-in location",
      severity: "High",
      status: "In review",
      assignedTo: "Amit Verma",
      openedAt: `${asOf}T09:18:00+05:30`,
      updatedAt: `${asOf}T10:05:00+05:30`,
      notes: [
        "Sign-in from Frankfurt, Germany – customer profile shows Mumbai as primary location.",
        "OTP verification was completed successfully.",
        "Customer contacted via registered mobile number – awaiting response.",
      ],
      riskScore: 76,
    },
    {
      id: "INV-0039",
      alertId: "FA-2039",
      customerId: "C1007",
      customerName: "Ishaan Patel",
      type: "Repeated login failures",
      severity: "Medium",
      status: "In review",
      assignedTo: "Priya Iyer",
      openedAt: `2026-10-04T17:20:00+05:30`,
      updatedAt: `${asOf}T08:30:00+05:30`,
      notes: [
        "Seven failed attempts from a single IP in Bengaluru.",
        "Account temporarily locked after the fifth attempt per security policy.",
        "No successful login from this IP in transaction history.",
      ],
      riskScore: 52,
    },
    {
      id: "INV-0038",
      alertId: "FA-2038",
      customerId: "C1001",
      customerName: "Aarav Shah",
      type: "Unrecognized device",
      severity: "Low",
      status: "Resolved",
      assignedTo: "Amit Verma",
      openedAt: `2026-10-03T11:35:00+05:30`,
      updatedAt: `2026-10-03T14:20:00+05:30`,
      notes: [
        "Login from a new iPad – OTP confirmed by customer.",
        "Customer confirmed ownership of device via support callback.",
        "Device added to trusted list. Alert closed as false positive.",
      ],
      riskScore: 18,
    },
    {
      id: "INV-0037",
      alertId: "FA-2037",
      customerId: "C1009",
      customerName: "Vivaan Desai",
      type: "High-value outflow",
      severity: "High",
      status: "Escalated",
      assignedTo: "Priya Iyer",
      openedAt: `2026-10-02T14:10:00+05:30`,
      updatedAt: `2026-10-04T09:00:00+05:30`,
      notes: [
        "₹12,00,000 transferred to a newly registered payee in 3 installments.",
        "Escalated to senior analyst for deeper review.",
        "Customer interview scheduled for 6 Oct 2026.",
      ],
      riskScore: 83,
      amount: 1200000,
    },
    {
      id: "INV-0036",
      alertId: "FA-2036",
      customerId: "C1011",
      customerName: "Arjun Singh",
      type: "Card misuse suspicion",
      severity: "Medium",
      status: "False positive",
      assignedTo: "Amit Verma",
      openedAt: `2026-10-01T10:00:00+05:30`,
      updatedAt: `2026-10-02T15:00:00+05:30`,
      notes: [
        "Card transaction flagged at a new merchant in Chennai.",
        "Customer confirmed the purchase was legitimate.",
        "Marked as false positive after customer verification.",
      ],
      riskScore: 30,
      amount: 8400,
    },
  ];
}

const STATUS_CLASS: Record<string, string> = {
  Open: "status-open",
  "In review": "status-in-review",
  Escalated: "risk-high",
  Resolved: "status-resolved",
  "False positive": "status-completed",
};

const PAGE_SIZE = 10;

export default function FraudInvestigation() {
  const { data, loading, error, refresh } = useAdminData();
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");
  const [assignee, setAssignee] = useState("all");
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<string | null>(null);

  const investigations = useMemo(
    () => (data ? generateInvestigations(data.asOf) : []),
    [data],
  );

  const filtered = useMemo(
    () =>
      investigations.filter(
        (inv) =>
          (severity === "all" || inv.severity === severity) &&
          (status === "all" || inv.status === status) &&
          (assignee === "all" || inv.assignedTo === assignee) &&
          (search === "" ||
            inv.id.toLowerCase().includes(search.toLowerCase()) ||
            inv.customerName.toLowerCase().includes(search.toLowerCase()) ||
            inv.type.toLowerCase().includes(search.toLowerCase()) ||
            inv.alertId.toLowerCase().includes(search.toLowerCase())),
      ),
    [investigations, severity, status, assignee, search],
  );

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;

  const openCount = investigations.filter(
    (i) => i.status === "Open" || i.status === "In review",
  ).length;
  const escalatedCount = investigations.filter(
    (i) => i.status === "Escalated",
  ).length;
  const resolvedCount = investigations.filter(
    (i) => i.status === "Resolved" || i.status === "False positive",
  ).length;
  const assignees = Array.from(
    new Set(investigations.map((i) => i.assignedTo)),
  );

  const inr = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  });

  function resetFilters() {
    setSearch("");
    setSeverity("all");
    setStatus("all");
    setAssignee("all");
    setPage(1);
  }

  return (
    <>
      <PageTitle
        title="Fraud Investigation"
        subtitle="Manage and track open fraud investigations, escalations and resolutions."
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
            <ScanSearch size={28} />
          </span>
          <div>
            <h2>
              {openCount} active investigation{openCount !== 1 ? "s" : ""} in
              progress.
            </h2>
            <p>
              {escalatedCount} escalated · {resolvedCount} closed in this cycle.
            </p>
          </div>
        </div>
        <Link href="/admin/fraud">
          Security monitoring <ArrowUpRight size={17} />
        </Link>
      </div>

      <div className="admin-stats four">
        <StatCard
          label="Open investigations"
          value={openCount}
          icon={ScanSearch}
          tone="amber"
          note="Active cases under review"
        />
        <StatCard
          label="Escalated"
          value={escalatedCount}
          icon={ShieldAlert}
          tone="red"
          note="Cases requiring senior analyst review"
        />
        <StatCard
          label="Resolved"
          value={resolvedCount}
          icon={CheckCircle}
          tone="green"
          note="Closed in the current monitoring period"
        />
        <StatCard
          label="Analysts assigned"
          value={assignees.length}
          icon={User}
          note="Analysts with active case assignments"
        />
      </div>

      <ChartCard
        title="Filter investigations"
        subtitle="Search and filter open, escalated and closed fraud cases"
      >
        <div className="admin-audit-search">
          <SearchBar
            value={search}
            onChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
            placeholder="Search by case ID, customer, alert or type…"
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
              { value: "Escalated", label: "Escalated" },
              { value: "Resolved", label: "Resolved" },
              { value: "False positive", label: "False positive" },
            ]}
            onChange={(v) => {
              setStatus(v);
              setPage(1);
            }}
          />
          <FilterDropdown
            label="Assigned analyst"
            value={assignee}
            options={[
              { value: "all", label: "All analysts" },
              ...assignees.map((a) => ({ value: a, label: a })),
            ]}
            onChange={(v) => {
              setAssignee(v);
              setPage(1);
            }}
          />
          <div />
        </div>
        <div className="admin-filter-caption">
          <span>
            {filtered.length} case{filtered.length !== 1 ? "s" : ""} match
            current filters
          </span>
          <button className="text-link" onClick={resetFilters}>
            <Filter size={12} /> Reset filters
          </button>
        </div>
      </ChartCard>

      <ChartCard
        title="Investigations"
        subtitle="All fraud cases with investigation notes and analyst assignments"
      >
        {paginated.length === 0 ? (
          <EmptyState
            title="No matching investigations"
            message="Try adjusting the search or filter options."
            onReset={resetFilters}
          />
        ) : (
          <>
            <div className="admin-investigations-list">
              {paginated.map((inv) => {
                const isExpanded = expanded === inv.id;
                return (
                  <div key={inv.id} className="admin-investigation-card">
                    <div className="admin-investigation-header">
                      <div className="admin-investigation-meta">
                        <div className="admin-investigation-ids">
                          <strong>{inv.id}</strong>
                          <small>↳ {inv.alertId}</small>
                        </div>
                        <div className="admin-investigation-info">
                          <Link
                            className="admin-table-link"
                            href={`/admin/customers/${inv.customerId}`}
                          >
                            <User size={12} />
                            {inv.customerName}
                          </Link>
                          <span className="admin-investigation-type">
                            {inv.type}
                          </span>
                          {inv.amount && (
                            <span className="admin-investigation-amount">
                              {inr.format(inv.amount)}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="admin-investigation-badges">
                        <RiskBadge risk={inv.severity} />
                        <span
                          className={`admin-badge ${STATUS_CLASS[inv.status] || ""}`}
                        >
                          {inv.status}
                        </span>
                        <span className="admin-badge">
                          <User size={10} />
                          {inv.assignedTo}
                        </span>
                        <span className="admin-badge admin-risk-number">
                          Risk {inv.riskScore}
                        </span>
                      </div>
                      <button
                        className="icon-button admin-investigation-toggle"
                        aria-label={
                          isExpanded
                            ? "Collapse case notes"
                            : "Expand case notes"
                        }
                        aria-expanded={isExpanded}
                        onClick={() => setExpanded(isExpanded ? null : inv.id)}
                      >
                        {isExpanded ? (
                          <ChevronUp size={18} />
                        ) : (
                          <ChevronDown size={18} />
                        )}
                      </button>
                    </div>

                    <div className="admin-investigation-timestamps">
                      <span>
                        <Clock size={11} /> Opened:{" "}
                        {localDate(inv.openedAt, true)} IST
                      </span>
                      <span>
                        <Clock size={11} /> Updated:{" "}
                        {localDate(inv.updatedAt, true)} IST
                      </span>
                    </div>

                    {isExpanded && (
                      <div className="admin-investigation-notes">
                        <div className="admin-investigation-notes-heading">
                          <MessageSquare size={14} /> Investigation notes
                        </div>
                        <ol className="admin-investigation-note-list">
                          {inv.notes.map((note, i) => (
                            <li key={i}>{note}</li>
                          ))}
                        </ol>
                        <div className="admin-investigation-actions">
                          <button className="button secondary small">
                            Mark in review
                          </button>
                          <button className="button secondary small">
                            Escalate
                          </button>
                          <button className="button secondary small">
                            Resolve
                          </button>
                          <button className="button secondary small">
                            False positive
                          </button>
                          <Link
                            className="text-link"
                            href={`/admin/customers/${inv.customerId}`}
                          >
                            View customer <ArrowUpRight size={14} />
                          </Link>
                        </div>
                        <p className="admin-investigation-disclaimer">
                          Sample data · Actions connect to backend API
                          integration pending.
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
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
