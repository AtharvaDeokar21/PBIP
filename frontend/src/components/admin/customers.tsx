"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAdminQuery } from "./use-admin-query";
import {
  Users,
  ShieldAlert,
  Landmark,
  ArrowUpRight,
  RefreshCw,
} from "lucide-react";
import { useAdminData } from "./use-admin-data";
import { activeAlerts } from "@/lib/admin/metrics";
import {
  PageTitle,
  StatCard,
  ChartCard,
  SearchBar,
  FilterDropdown,
  DataTable,
  Pagination,
  RiskBadge,
  EmptyState,
  LoadingState,
  ErrorState,
} from "./ui";
const all = (values: string[]) => [
  { value: "all", label: "All" },
  ...values.map((value) => ({ value, label: value })),
];
export default function Customers() {
  const {
    params,
    update: updateQuery,
    reset,
  } = useAdminQuery("/admin/customers");
  const router = useRouter();
  const { data, loading, error, refresh } = useAdminData();
  const search = params.get("q") || "";
  const risk = params.get("risk") || "all";
  const alert = params.get("alerts") || "all";
  const segment = params.get("segment") || "all";
  const sort = params.get("sort") || "name";
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(5);
  function update(key: string, value: string) {
    setPage(1);
    updateQuery(key, value);
  }
  function clear() {
    setPage(1);
    reset();
  }
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;
  const filtered = data.customers
    .filter(
      (c) =>
        `${c.name} ${c.id} ${c.email}`
          .toLowerCase()
          .includes(search.toLowerCase()) &&
        (risk === "all" || risk === c.risk) &&
        (segment === "all" || segment === c.segment) &&
        (alert === "all" ||
          (alert === "active"
            ? activeAlerts(data, c.id).length > 0
            : activeAlerts(data, c.id).length === 0)),
    )
    .sort((a, b) =>
      sort === "risk"
        ? b.riskScore - a.riskScore
        : a.name.localeCompare(b.name),
    );
  const current = Math.min(
    page,
    Math.max(1, Math.ceil(filtered.length / size)),
  );
  const rows = filtered.slice((current - 1) * size, current * size);
  return (
    <>
      <PageTitle
        title="Customers"
        subtitle="Search and review customer banking and behavioural information."
        action={
          <button className="button secondary small" onClick={refresh}>
            <RefreshCw size={15} /> Refresh
          </button>
        }
      />
      <div className="admin-stats three">
        <StatCard
          label="Customer directory"
          value={data.customers.length}
          icon={Users}
          note="Individual customer profiles"
        />
        <StatCard
          label="Customers with active alerts"
          value={
            data.customers.filter((c) => activeAlerts(data, c.id).length).length
          }
          icon={ShieldAlert}
          note="Fraud and compliance signals"
          tone="amber"
        />
        <StatCard
          label="Active accounts"
          value={data.customers.reduce(
            (sum, c) =>
              sum +
              c.accounts.filter((account) => account.status === "Active").length,
            0,
          )}
          icon={Landmark}
          note="Accounts with active status"
        />
      </div>
      <ChartCard
        title="Customer directory"
        subtitle={`${filtered.length} matching ${filtered.length === 1 ? "customer" : "customers"}`}
        action={
          <button className="text-link" onClick={clear}>
            Clear filters
          </button>
        }
      >
        <div className="admin-directory-search">
          <SearchBar value={search} onChange={(value) => update("q", value)} />
        </div>
        <div className="admin-filters">
          <FilterDropdown
            label="Risk level"
            value={risk}
            options={all(["Low", "Medium", "High"])}
            onChange={(value) => update("risk", value)}
          />
          <FilterDropdown
            label="Fraud / alert status"
            value={alert}
            options={[
              { value: "all", label: "All" },
              { value: "none", label: "No active alerts" },
              { value: "active", label: "Active alert" },
            ]}
            onChange={(value) => update("alerts", value)}
          />
          <FilterDropdown
            label="Customer segment"
            value={segment}
            options={all(["Standard", "Premium", "High Value"])}
            onChange={(value) => update("segment", value)}
          />
          <FilterDropdown
            label="Sort by"
            value={sort}
            options={[
              { value: "name", label: "Name A–Z" },
              { value: "risk", label: "Highest risk score" },
            ]}
            onChange={(value) => update("sort", value)}
          />
        </div>
        {rows.length ? (
          <DataTable
            label="Customer directory"
            headings={[
              "Customer",
              "Email",
              "Account type",
              "Segment",
              "Risk",
              "Active alerts",
              "Action",
            ]}
          >
            {rows.map((c) => (
              <tr
                key={c.id}
                className="admin-clickable-row"
                onClick={() => router.push(`/admin/customers/${c.id}`)}
              >
                <td>
                  <div className="admin-customer-cell">
                    <span className="admin-customer-avatar">
                      {c.name
                        .split(" ")
                        .map((part) => part[0])
                        .join("")}
                    </span>
                    <span>
                      <strong>{c.name}</strong>
                      <small>{c.id}</small>
                    </span>
                  </div>
                </td>
                <td>{c.email}</td>
                <td>{c.accounts.map((a) => a.type).join(", ")}</td>
                <td>
                  <span className="admin-segment">{c.segment}</span>
                </td>
                <td>
                  <RiskBadge risk={c.risk} />
                </td>
                <td>
                  <span
                    className={`admin-alert-count ${activeAlerts(data, c.id).length ? "has-alerts" : ""}`}
                  >
                    {activeAlerts(data, c.id).length}
                  </span>
                </td>
                <td>
                  <Link
                    href={`/admin/customers/${c.id}`}
                    className="admin-table-link"
                    aria-label={`View details for ${c.name}`}
                  >
                    View details <ArrowUpRight size={14} />
                  </Link>
                </td>
              </tr>
            ))}
          </DataTable>
        ) : (
          <EmptyState onReset={clear} />
        )}
        <div className="admin-directory-footer">
          <FilterDropdown
            label="Rows per page"
            value={String(size)}
            options={[5, 10, 20].map((n) => ({
              value: String(n),
              label: String(n),
            }))}
            onChange={(value) => {
              setSize(Number(value));
              setPage(1);
            }}
          />
          <Pagination
            page={current}
            size={size}
            total={filtered.length}
            onChange={setPage}
          />
        </div>
      </ChartCard>
    </>
  );
}
