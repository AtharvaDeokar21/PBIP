"use client";
import Link from "next/link";
import { useState, useMemo, useEffect, useCallback, useRef } from "react";
import {
  ScanSearch,
  ShieldAlert,
  RefreshCw,
  ArrowUpRight,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  User,
  MessageSquare,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAdminData } from "./use-admin-data";
import {
  PageTitle,
  AdminHeaderDate,
  ChartCard,
  RiskBadge,
  FilterDropdown,
  SearchBar,
  EmptyState,
  LoadingState,
  ErrorState,
  StatCard,
  Pagination,
} from "./ui";
import { activeAlerts, localDate } from "@/lib/admin/metrics";
import type {
  InvestigationItem,
  Alert,
  CanonicalAlertStatus,
  InvestigationStatus,
} from "@/lib/admin/types";
import {
  fetchFraudInvestigations,
  updateFraudAlertStatus,
} from "@/lib/admin/api";

const STATUS_CLASS: Record<string, string> = {
  Open: "status-open",
  "In review": "status-in-review",
  Escalated: "risk-high",
  Resolved: "status-resolved",
  "False positive": "status-completed",
};

const PAGE_SIZE = 10;

function isActionAllowed(
  currentStatus: InvestigationStatus,
  target: CanonicalAlertStatus,
): boolean {
  switch (currentStatus) {
    case "Open":
      return target === "IN_REVIEW" || target === "ESCALATED";
    case "In review":
      return (
        target === "ESCALATED" ||
        target === "RESOLVED" ||
        target === "FALSE_POSITIVE"
      );
    case "Escalated":
      return (
        target === "IN_REVIEW" ||
        target === "RESOLVED" ||
        target === "FALSE_POSITIVE"
      );
    case "Resolved":
    case "False positive":
      return target === "IN_REVIEW";
    default:
      return false;
  }
}

function parseApiError(err: unknown): string {
  if (err instanceof Error) {
    const message = err.message;
    const match = message.match(/^API \d+: (.*)$/);
    if (match && match[1]) {
      try {
        const parsed = JSON.parse(match[1]);
        if (typeof parsed.detail === "string") {
          return parsed.detail;
        }
        if (Array.isArray(parsed.detail) && parsed.detail[0]?.msg) {
          return parsed.detail[0].msg;
        }
      } catch {
        return match[1];
      }
    }
    return message;
  }
  return "An unexpected error occurred while updating the case.";
}

export default function FraudInvestigation() {
  const { data: adminData, loading: adminLoading, error: adminError, refresh: refreshAdmin } = useAdminData();
  const [investigations, setInvestigations] = useState<InvestigationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");
  const [assignee, setAssignee] = useState("all");
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [allAssignees, setAllAssignees] = useState<string[]>([]);
  const [updatingAlertId, setUpdatingAlertId] = useState<string | null>(null);
  const [updatingTargetStatus, setUpdatingTargetStatus] =
    useState<CanonicalAlertStatus | null>(null);
  const [actionFeedback, setActionFeedback] = useState<{
    alertId: string;
    type: "success" | "error";
    message: string;
  } | null>(null);

  const requestIdRef = useRef(0);

  // Debounce search input to avoid requests on every keystroke
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  // Fetch full assignee list once (or when admin data changes) for dropdown options
  useEffect(() => {
    let active = true;
    fetchFraudInvestigations(new URLSearchParams({ page: "1", page_size: "100" }))
      .then((res) => {
        if (!active) return;
        const distinct = Array.from(new Set(res.items.map((i) => i.assignedTo).filter(Boolean)));
        setAllAssignees(distinct);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  // Server-side filtered and paginated fetch
  const loadInvestigations = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;
    setLoading(true);
    setError("");

    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    });

    if (severity !== "all") params.set("severity", severity);
    if (status !== "all") params.set("status", status);
    if (assignee !== "all") params.set("assignee", assignee);
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());

    try {
      const res = await fetchFraudInvestigations(params);
      if (currentRequestId === requestIdRef.current) {
        setInvestigations(res.items);
        setTotal(res.total);
      }
    } catch (err: unknown) {
      if (currentRequestId === requestIdRef.current) {
        setError(err instanceof Error ? err.message : "Failed to load fraud investigations from server.");
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [page, severity, status, assignee, debouncedSearch]);

  useEffect(() => {
    loadInvestigations();
  }, [loadInvestigations]);

  const refreshAll = useCallback(() => {
    refreshAdmin();
    loadInvestigations();
  }, [refreshAdmin, loadInvestigations]);

  const handleStatusUpdate = useCallback(
    async (alertId: string, targetStatus: CanonicalAlertStatus) => {
      setUpdatingAlertId(alertId);
      setUpdatingTargetStatus(targetStatus);
      setActionFeedback(null);

      try {
        await updateFraudAlertStatus(alertId, { status: targetStatus });
        const targetLabel =
          targetStatus === "IN_REVIEW"
            ? "In review"
            : targetStatus === "ESCALATED"
            ? "Escalated"
            : targetStatus === "RESOLVED"
            ? "Resolved"
            : "False positive";

        setActionFeedback({
          alertId,
          type: "success",
          message: `Case status successfully updated to ${targetLabel}.`,
        });

        // Refresh both investigations list and overview summary data
        await Promise.all([loadInvestigations(), refreshAdmin()]);
      } catch (err: unknown) {
        const errorMsg = parseApiError(err);
        setActionFeedback({
          alertId,
          type: "error",
          message: errorMsg,
        });
      } finally {
        setUpdatingAlertId(null);
        setUpdatingTargetStatus(null);
      }
    },
    [loadInvestigations, refreshAdmin],
  );

  // Derive stat banner and cards from the current snapshot
  const activeFraudAlerts = useMemo(
    () => (adminData ? activeAlerts(adminData).filter((a: Alert) => a.domain === "Fraud") : []),
    [adminData],
  );
  const openCount = useMemo(
    () => activeFraudAlerts.filter((a: Alert) => a.status === "Open" || a.status === "In review").length,
    [activeFraudAlerts],
  );
  const activeAlertsCount = activeFraudAlerts.length;
  const highRiskCount = useMemo(
    () => (adminData ? adminData.customers.filter((c) => c.risk === "High" || c.risk === "Critical").length : 0),
    [adminData],
  );

  const inr = useMemo(
    () =>
      new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
      }),
    [],
  );

  function resetFilters() {
    setSearch("");
    setDebouncedSearch("");
    setSeverity("all");
    setStatus("all");
    setAssignee("all");
    setPage(1);
    setActionFeedback(null);
  }

  if (adminLoading) return <LoadingState />;
  if (adminError || !adminData) {
    return <ErrorState message={adminError || "Unable to load dashboard data."} retry={refreshAll} />;
  }

  return (
    <>
      <PageTitle
        title="Fraud Investigation"
        subtitle="Manage and track open fraud investigations, escalations and resolutions."
        action={
          <div className="admin-title-actions">
            <AdminHeaderDate snapshotDate={adminData.asOf} />
            <button className="button secondary small" onClick={refreshAll}>
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
              {openCount} active investigation{openCount !== 1 ? "s" : ""} in progress.
            </h2>
            <p>
              {activeAlertsCount} active fraud alert{activeAlertsCount !== 1 ? "s" : ""} · {highRiskCount} high-risk customer{highRiskCount !== 1 ? "s" : ""}.
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
          label="Active fraud alerts"
          value={activeAlertsCount}
          icon={ShieldAlert}
          tone="red"
          note="Unresolved security detections"
        />
        <StatCard
          label="High-risk customers"
          value={highRiskCount}
          icon={CheckCircle}
          tone="green"
          note="Customers with elevated risk profiles"
        />
        <StatCard
          label="Analysts assigned"
          value={allAssignees.length}
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
              ...allAssignees.map((a) => ({ value: a, label: a })),
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
            {total} case{total !== 1 ? "s" : ""} match current filters
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
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} retry={loadInvestigations} />
        ) : investigations.length === 0 ? (
          <EmptyState
            title="No matching investigations"
            message="Try adjusting the search or filter options."
            onReset={resetFilters}
          />
        ) : (
          <>
            <div className="admin-investigations-list">
              {investigations.map((inv) => {
                const isExpanded = expanded === inv.id;
                const isUpdatingThisAlert = updatingAlertId === inv.alertId;
                const canMarkInReview = isActionAllowed(inv.status, "IN_REVIEW");
                const canEscalate = isActionAllowed(inv.status, "ESCALATED");
                const canResolve = isActionAllowed(inv.status, "RESOLVED");
                const canMarkFalsePositive = isActionAllowed(
                  inv.status,
                  "FALSE_POSITIVE",
                );
                return (
                  <div key={inv.id} className="admin-investigation-card">
                    <div className="admin-investigation-header">
                      <div className="admin-investigation-meta">
                        <div className="admin-investigation-ids">
                          <strong>{inv.id}</strong>
                          <small>↳ {inv.alertId}</small>
                        </div>
                        <div className="admin-investigation-info">
                          {inv.customerId ? (
                            <Link
                              className="admin-table-link"
                              href={`/admin/customers/${inv.customerId}`}
                            >
                              <User size={12} />
                              {inv.customerName}
                            </Link>
                          ) : (
                            <span className="admin-investigation-customer-name">
                              <User size={12} />
                              {inv.customerName}
                            </span>
                          )}
                          <span className="admin-investigation-type">
                            {inv.type}
                          </span>
                          {inv.amount != null && (
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
                        {inv.notes && inv.notes.length > 0 ? (
                          <ol className="admin-investigation-note-list">
                            {inv.notes.map((note, i) => (
                              <li key={i}>{note}</li>
                            ))}
                          </ol>
                        ) : (
                          <p style={{ color: "#8a94a6", fontSize: "0.85rem", fontStyle: "italic", margin: "0.5rem 0" }}>
                            No notes recorded for this investigation.
                          </p>
                        )}
                        <div className="admin-investigation-actions">
                          <button
                            className="button secondary small"
                            disabled={isUpdatingThisAlert || !canMarkInReview}
                            title={
                              inv.status === "In review"
                                ? "Case is already in review"
                                : isUpdatingThisAlert
                                ? "Updating case status..."
                                : "Mark case in review"
                            }
                            onClick={() =>
                              handleStatusUpdate(inv.alertId, "IN_REVIEW")
                            }
                          >
                            {isUpdatingThisAlert &&
                            updatingTargetStatus === "IN_REVIEW"
                              ? "Updating..."
                              : "Mark in review"}
                          </button>
                          <button
                            className="button secondary small"
                            disabled={isUpdatingThisAlert || !canEscalate}
                            title={
                              inv.status === "Escalated"
                                ? "Case is already escalated"
                                : inv.status === "Resolved" ||
                                  inv.status === "False positive"
                                ? "Reopen case in review before escalating"
                                : isUpdatingThisAlert
                                ? "Updating case status..."
                                : "Escalate case for senior review"
                            }
                            onClick={() =>
                              handleStatusUpdate(inv.alertId, "ESCALATED")
                            }
                          >
                            {isUpdatingThisAlert &&
                            updatingTargetStatus === "ESCALATED"
                              ? "Updating..."
                              : "Escalate"}
                          </button>
                          <button
                            className="button secondary small"
                            disabled={isUpdatingThisAlert || !canResolve}
                            title={
                              inv.status === "Open"
                                ? "Case must be in review before resolution"
                                : inv.status === "Resolved"
                                ? "Case is already resolved"
                                : inv.status === "False positive"
                                ? "Case is already closed as false positive"
                                : isUpdatingThisAlert
                                ? "Updating case status..."
                                : "Resolve case"
                            }
                            onClick={() =>
                              handleStatusUpdate(inv.alertId, "RESOLVED")
                            }
                          >
                            {isUpdatingThisAlert &&
                            updatingTargetStatus === "RESOLVED"
                              ? "Updating..."
                              : "Resolve"}
                          </button>
                          <button
                            className="button secondary small"
                            disabled={
                              isUpdatingThisAlert || !canMarkFalsePositive
                            }
                            title={
                              inv.status === "Open"
                                ? "Case must be in review before resolution"
                                : inv.status === "False positive"
                                ? "Case is already closed as false positive"
                                : inv.status === "Resolved"
                                ? "Case is already resolved"
                                : isUpdatingThisAlert
                                ? "Updating case status..."
                                : "Mark alert as false positive"
                            }
                            onClick={() =>
                              handleStatusUpdate(inv.alertId, "FALSE_POSITIVE")
                            }
                          >
                            {isUpdatingThisAlert &&
                            updatingTargetStatus === "FALSE_POSITIVE"
                              ? "Updating..."
                              : "False positive"}
                          </button>
                          {inv.customerId ? (
                            <Link
                              className="text-link"
                              href={`/admin/customers/${inv.customerId}`}
                            >
                              View customer <ArrowUpRight size={14} />
                            </Link>
                          ) : null}
                        </div>
                        {actionFeedback &&
                          actionFeedback.alertId === inv.alertId && (
                            <div
                              role="status"
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "6px",
                                fontSize: "0.8rem",
                                padding: "6px 10px",
                                borderRadius: "6px",
                                marginBottom: "8px",
                                backgroundColor:
                                  actionFeedback.type === "success"
                                    ? "#f0fdf4"
                                    : "#fef2f2",
                                color:
                                  actionFeedback.type === "success"
                                    ? "#166534"
                                    : "#991b1b",
                                border: `1px solid ${
                                  actionFeedback.type === "success"
                                    ? "#bbf7d0"
                                    : "#fecaca"
                                }`,
                              }}
                            >
                              {actionFeedback.type === "success" ? (
                                <CheckCircle
                                  size={14}
                                  style={{ flexShrink: 0 }}
                                />
                              ) : (
                                <AlertCircle
                                  size={14}
                                  style={{ flexShrink: 0 }}
                                />
                              )}
                              <span>{actionFeedback.message}</span>
                            </div>
                          )}
                        <p className="admin-investigation-disclaimer">
                          Connected to real alerts · Changes are logged to system audit.
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
