"use client";
import Link from "next/link";
import { useAdminQuery } from "./use-admin-query";
import {
  Users,
  Clock,
  TrendingUp,
  Activity,
  ArrowUpRight,
  X,
} from "lucide-react";
import { useAdminData } from "./use-admin-data";
import {
  mean,
  duration,
  engagement,
  periodBounds,
  localDate,
} from "@/lib/admin/metrics";
import {
  PageTitle,
  StatCard,
  ChartCard,
  FilterDropdown,
  DataTable,
  RiskBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  HorizontalBars,
  MiniTrend,
} from "./ui";
const all = (values: string[]) => [
  { value: "all", label: "All" },
  ...values.map((value) => ({ value, label: value })),
];
export default function Analytics() {
  const { params, update, reset } = useAdminQuery("/admin/analytics");
  const { data, loading, error, refresh } = useAdminData();
  const period = params.get("period") || "30";
  const segment = params.get("segment") || "all";
  const product = params.get("product") || "all";
  const customerId = params.get("customer") || "all";
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;
  const bounds = periodBounds(period, data.asOf);
  const from = period === "custom" ? params.get("from") || "" : bounds.from;
  const to = period === "custom" ? params.get("to") || "" : bounds.to;
  const valid = Boolean(from && to && from <= to);
  const candidates = data.customers.filter(
    (c) =>
      (customerId === "all" || c.id === customerId) &&
      (segment === "all" || c.segment === segment) &&
      (product === "all" || c.interest === product),
  );
  const candidateIds = new Set(candidates.map((c) => c.id));
  const sessions = valid
    ? data.sessions.filter(
        (s) =>
          candidateIds.has(s.customerId) &&
          s.date >= from &&
          s.date <= to &&
          (product === "all" || s.product === product),
      )
    : [];
  const activeIds = new Set(sessions.map((s) => s.customerId));
  const customers = candidates.filter((c) => activeIds.has(c.id));
  const productRows = ["Savings", "Loans", "Investments", "Insurance"]
    .map((label) => {
      const records = sessions.filter((s) => s.product === label);
      return {
        label,
        value: records.reduce((sum, s) => sum + s.views, 0),
        clicks: records.reduce((sum, s) => sum + s.clicks, 0),
        customers: new Set(records.map((s) => s.customerId)).size,
        engagement: engagement(records),
      };
    })
    .sort((a, b) => b.value - a.value);
  const pageNames = Array.from(new Set(sessions.flatMap((s) => s.path)));
  const pageRows = pageNames
    .map((label) => {
      const records = sessions.filter((s) => s.path.includes(label));
      return {
        label,
        visits: records.length,
        customers: new Set(records.map((s) => s.customerId)).size,
        seconds: mean(records.map((s) => s.seconds / s.path.length)),
      };
    })
    .sort((a, b) => b.visits - a.visits);
  const flowNames = Array.from(
    new Set(sessions.map((s) => s.path.join(" → "))),
  );
  const transactionRows = data.transactions.filter(
    (t) => activeIds.has(t.customerId) && t.date >= from && t.date <= to,
  );
  function topSpendingCategory(customerId: string) {
    const totals = new Map<string, number>();
    transactionRows
      .filter((t) => t.customerId === customerId && t.type === "Debit")
      .forEach((t) => {
        totals.set(t.category, (totals.get(t.category) || 0) + t.amount);
      });
    return [...totals.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || "No spending recorded";
  }
  const spendingRows = [
    "Food",
    "Shopping",
    "Travel",
    "Utilities",
    "Entertainment",
    "Other",
  ].map((label) => ({
    label,
    value: transactionRows
      .filter((t) => t.type === "Debit" && t.category === label)
      .reduce((sum, t) => sum + t.amount, 0),
  }));
  const months = Array.from(
    new Set(sessions.map((s) => s.date.slice(0, 7))),
  ).sort();
  return (
    <>
      <PageTitle
        title="Behaviour analytics"
        subtitle="Understand how customers engage, explore and manage their financial everyday."
      />
      <ChartCard
        title="Explore your customer base"
        subtitle={`Records available through ${localDate(data.asOf)} · Filters apply across all sections`}
      >
        <div className="admin-filters analytics">
          <FilterDropdown
            label="Date range"
            value={period}
            options={[
              { value: "7", label: "Last 7 days" },
              { value: "30", label: "Last 30 days" },
              { value: "90", label: "Last 3 months" },
              { value: "custom", label: "Custom range" },
            ]}
            onChange={(value) => update("period", value)}
          />
          <FilterDropdown
            label="Customer segment"
            value={segment}
            options={all(["Standard", "Premium", "High Value"])}
            onChange={(value) => update("segment", value)}
          />
          <FilterDropdown
            label="Product interest"
            value={product}
            options={all(["Loans", "Savings", "Investments", "Insurance"])}
            onChange={(value) => update("product", value)}
          />
          <FilterDropdown
            label="Customer"
            value={customerId}
            options={[
              { value: "all", label: "All customers" },
              ...data.customers.map((c) => ({ value: c.id, label: c.name })),
            ]}
            onChange={(value) => update("customer", value)}
          />
        </div>
        {period === "custom" && (
          <div className="admin-custom-dates">
            <label>
              From
              <input
                aria-label="Analytics from date"
                type="date"
                value={from}
                max={data.asOf}
                onChange={(e) => update("from", e.target.value)}
              />
            </label>
            <label>
              To
              <input
                aria-label="Analytics to date"
                type="date"
                value={to}
                min={from}
                max={data.asOf}
                onChange={(e) => update("to", e.target.value)}
              />
            </label>
            {!valid && (
              <p role="alert">
                Choose both dates; the end must be on or after the start.
              </p>
            )}
          </div>
        )}
        {customerId !== "all" && (
          <div className="admin-selection">
            <span>
              Customer:{" "}
              <strong>
                {data.customers.find((c) => c.id === customerId)?.name ||
                  customerId}
              </strong>
            </span>
            <button
              className="text-link"
              onClick={() => update("customer", "all")}
            >
              <X size={14} /> Clear customer
            </button>
          </div>
        )}
        <div className="admin-filter-caption">
          <span>
            {valid
              ? `${localDate(from)} – ${localDate(to)}`
              : "Select a valid date range"}
          </span>
          <button className="text-link" onClick={reset}>
            Reset filters
          </button>
        </div>
      </ChartCard>
      <div className="admin-stats four">
        <StatCard
          label="Active customers"
          value={customers.length}
          icon={Users}
          note="Unique customers in selected sessions"
        />
        <StatCard
          label="Average session"
          value={duration(mean(sessions.map((s) => s.seconds)))}
          icon={Clock}
          note="Time spent across selected sessions"
        />
        <StatCard
          label="Most interested product"
          value={sessions.length ? productRows[0].label : "—"}
          icon={TrendingUp}
          note="Highest recorded product views"
        />
        <StatCard
          label="Average engagement"
          value={`${engagement(sessions)}%`}
          icon={Activity}
          note="Average session click-to-view ratio"
        />
      </div>
      {!sessions.length ? (
        <ChartCard title="No activity in this selection">
          <EmptyState
            message="Choose another period, segment, product or customer to view recorded activity."
            onReset={reset}
          />
        </ChartCard>
      ) : (
        <>
          <div className="admin-grid three">
            <ChartCard
              title="Customer segmentation"
              subtitle="Active customers in the selected period"
            >
              <HorizontalBars
                rows={["Standard", "Premium", "High Value"].map((label) => ({
                  label,
                  value: customers.filter((c) => c.segment === label).length,
                }))}
              />
            </ChartCard>
            <ChartCard
              title="Spending patterns"
              subtitle="Recorded debit amounts within the selected dates"
            >
              {spendingRows.some((row) => row.value > 0) ? (
                <HorizontalBars rows={spendingRows} money />
              ) : (
                <EmptyState
                  title="No recorded debit transactions"
                  message="There are sessions but no debit records in this date range."
                />
              )}
            </ChartCard>
            <ChartCard
              title="Income patterns"
              subtitle="Income baseline of active customer profiles"
            >
              <HorizontalBars
                rows={[
                  {
                    label: "Below ₹75,000",
                    value: customers.filter((c) => c.income < 75000).length,
                  },
                  {
                    label: "₹75,000–₹1,25,000",
                    value: customers.filter(
                      (c) => c.income >= 75000 && c.income <= 125000,
                    ).length,
                  },
                  {
                    label: "Above ₹1,25,000",
                    value: customers.filter((c) => c.income > 125000).length,
                  },
                ]}
              />
              <p className="admin-chart-caption">
                Income bands reflect profile baselines for active customers in
                the selected period.
              </p>
            </ChartCard>
          </div>
          <div className="admin-grid two">
            <ChartCard
              title="Product interest & affinity"
              subtitle="Views and clicks from selected session records"
            >
              <DataTable
                label="Product affinity"
                headings={[
                  "Product",
                  "Views",
                  "Clicks",
                  "Interested customers",
                  "Engagement",
                ]}
              >
                {productRows.map((row) => (
                  <tr key={row.label}>
                    <td>
                      <strong>{row.label}</strong>
                    </td>
                    <td>{row.value}</td>
                    <td>{row.clicks}</td>
                    <td>{row.customers}</td>
                    <td>{row.engagement}%</td>
                  </tr>
                ))}
              </DataTable>
            </ChartCard>
            <ChartCard
              title="Session analytics"
              subtitle="Interaction depth and return visits"
            >
              <div className="admin-session-metrics">
                <div>
                  <span>Total sessions</span>
                  <strong>{sessions.length}</strong>
                </div>
                <div>
                  <span>Pages per session</span>
                  <strong>
                    {mean(sessions.map((s) => s.path.length)).toFixed(1)}
                  </strong>
                </div>
                <div>
                  <span>Returning customers</span>
                  <strong>
                    {
                      new Set(
                        sessions
                          .filter((s) => s.returning)
                          .map((s) => s.customerId),
                      ).size
                    }
                  </strong>
                </div>
                <div>
                  <span>Average duration</span>
                  <strong>
                    {duration(mean(sessions.map((s) => s.seconds)))}
                  </strong>
                </div>
              </div>
              <MiniTrend
                rows={months.map((month) => ({
                  label: new Intl.DateTimeFormat("en-IN", {
                    month: "short",
                    timeZone: "Asia/Kolkata",
                  }).format(new Date(`${month}-01T12:00:00+05:30`)),
                  value: sessions.filter((s) => s.date.startsWith(month))
                    .length,
                }))}
              />
              <p className="admin-chart-caption">
                Recorded sessions by month; partial periods reflect the chosen
                dates.
              </p>
            </ChartCard>
          </div>
          <div className="admin-grid two">
            <ChartCard
              title="Page visits"
              subtitle="Time is estimated as session duration divided by visited pages"
            >
              <DataTable
                label="Page visits"
                headings={["Page", "Visits", "Unique customers", "Avg. time"]}
              >
                {pageRows.map((row) => (
                  <tr key={row.label}>
                    <td>{row.label}</td>
                    <td>{row.visits}</td>
                    <td>{row.customers}</td>
                    <td>{duration(row.seconds)}</td>
                  </tr>
                ))}
              </DataTable>
            </ChartCard>
            <ChartCard
              title="Common navigation journeys"
              subtitle="Simplified clickstream activity"
            >
              <div className="admin-flow-list">
                {flowNames.map((path) => (
                  <div key={path}>
                    <div>
                      {path.split(" → ").map((step, i) => (
                        <span key={step}>
                          {i > 0 && <span className="admin-flow-arrow">→</span>}
                          <b>{step}</b>
                        </span>
                      ))}
                    </div>
                    <small>
                      {
                        sessions.filter((s) => s.path.join(" → ") === path)
                          .length
                      }{" "}
                      sessions
                    </small>
                  </div>
                ))}
              </div>
            </ChartCard>
          </div>
          <ChartCard
            title="Customer behaviour"
            subtitle="View a profile to connect engagement with banking and risk information"
          >
            <DataTable
              label="Customer behaviour"
              headings={[
                "Customer",
                "Segment",
                "Product interest",
                "Avg. session",
                "Engagement",
                "Top spending category",
                "Risk",
                "Action",
              ]}
            >
              {customers.map((c) => {
                const records = sessions.filter((s) => s.customerId === c.id);
                return (
                  <tr key={c.id}>
                    <td>
                      <strong>{c.name}</strong>
                      <small>{c.id}</small>
                    </td>
                    <td>{c.segment}</td>
                    <td>{c.interest}</td>
                    <td>{duration(mean(records.map((s) => s.seconds)))}</td>
                    <td>{engagement(records)}%</td>
                    <td>{topSpendingCategory(c.id)}</td>
                    <td>
                      <RiskBadge risk={c.risk} />
                    </td>
                    <td>
                      <Link
                        className="admin-table-link"
                        href={`/admin/customers/${c.id}`}
                        aria-label={`View customer ${c.name}`}
                      >
                        View customer <ArrowUpRight size={14} />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </DataTable>
          </ChartCard>
        </>
      )}
    </>
  );
}
