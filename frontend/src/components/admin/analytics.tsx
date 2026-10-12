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
import { useBehaviourAnalytics } from "./use-behaviour-analytics";
import { duration, engagement, periodBounds, localDate } from "@/lib/admin/metrics";
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

function mean(arr: number[]) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

export default function Analytics() {
  const { params, update, reset } = useAdminQuery("/admin/analytics");

  const period = params.get("period") || "30";
  const segment = params.get("segment") || "all";
  const product = params.get("product") || "all";
  const customerId = params.get("customer") || "all";
  const dateHint = new Date().toISOString().slice(0, 10);
  const bounds = periodBounds(period, dateHint);
  const from =
    period === "custom" ? params.get("from") || "" : bounds.from;
  const to = period === "custom" ? params.get("to") || "" : bounds.to;
  const valid = Boolean(from && to && from <= to);

  // Build API params from UI state
  const apiParams = new URLSearchParams({ page_size: "50" });
  if (valid) {
    apiParams.set("date_from", from);
    apiParams.set("date_to", to);
  }
  if (segment !== "all") apiParams.set("segment", segment);
  if (product !== "all") apiParams.set("product", product);
  if (customerId !== "all") apiParams.set("customer_id", customerId);

  const { data, filters, loading, error, refresh } = useBehaviourAnalytics(apiParams);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;

  const asOf = data.data_available_through;

  // KPIs direct from backend
  const kpis = data.kpis;

  // Customer list from behaviour items
  const customers = data.customer_behaviour.items;

  // Sessions by month for trend chart
  const months = data.session_analytics.sessions_by_month;

  // Segmentation
  const segRows = data.segmentation.map((s) => ({ label: s.segment, value: s.count }));

  // Spending patterns
  const spendRows = data.spending_patterns.map((s) => ({ label: s.category, value: s.amount }));

  // Income bands
  const incomeRows = data.income_patterns.map((b) => ({ label: b.band, value: b.count }));

  // Product affinity
  const affinityRows = data.product_affinity;

  // Page visits
  const pageRows = data.page_visits;

  // Navigation journeys
  const journeyRows = data.navigation_journeys;

  const hasSessions = data.session_analytics.total_sessions > 0;

  // Customer filter options
  const customerOptions = [
    { value: "all", label: "All customers" },
    ...(filters?.customers ?? []).map((c) => ({ value: c.id, label: c.name })),
  ];

  const segmentOptions = all(filters?.segments ?? ["Standard", "Premium", "High Value"]);
  const productOptions = all(filters?.products ?? ["Savings", "Loans", "Investments", "Insurance"]);

  return (
    <>
      <PageTitle
        title="Behaviour analytics"
        subtitle="Understand how customers engage, explore and manage their financial everyday."
      />
      <ChartCard
        title="Explore your customer base"
        subtitle={`Records available through ${localDate(asOf)} · Filters apply across all sections`}
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
            options={segmentOptions}
            onChange={(value) => update("segment", value)}
          />
          <FilterDropdown
            label="Product interest"
            value={product}
            options={productOptions}
            onChange={(value) => update("product", value)}
          />
          <FilterDropdown
            label="Customer"
            value={customerId}
            options={customerOptions}
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
                max={asOf}
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
                max={asOf}
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
                {filters?.customers.find((c) => c.id === customerId)?.name ?? customerId}
              </strong>
            </span>
            <button className="text-link" onClick={() => update("customer", "all")}>
              <X size={14} /> Clear customer
            </button>
          </div>
        )}
        <div className="admin-filter-caption">
          <span>
            {valid ? `${localDate(from)} – ${localDate(to)}` : "Select a valid date range"}
          </span>
          <button className="text-link" onClick={reset}>
            Reset filters
          </button>
        </div>
      </ChartCard>

      {/* KPI Cards */}
      <div className="admin-stats four">
        <StatCard
          label="Active customers"
          value={kpis.active_customers}
          icon={Users}
          note="Unique customers in selected period"
        />
        <StatCard
          label="Average session"
          value={duration(kpis.avg_session_seconds)}
          icon={Clock}
          note="Average session duration"
        />
        <StatCard
          label="Most interested product"
          value={kpis.most_interested_product ?? "—"}
          icon={TrendingUp}
          note="Highest recorded product views"
        />
        <StatCard
          label="Average engagement"
          value={`${kpis.avg_engagement_pct}%`}
          icon={Activity}
          note="Average session click-to-view ratio"
        />
      </div>

      {!hasSessions ? (
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
              <HorizontalBars rows={segRows.length ? segRows : [{ label: "No data", value: 0 }]} />
            </ChartCard>
            <ChartCard
              title="Spending patterns"
              subtitle="Recorded debit amounts within the selected dates"
            >
              {spendRows.some((r) => r.value > 0) ? (
                <HorizontalBars rows={spendRows} money />
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
              <HorizontalBars rows={incomeRows.length ? incomeRows : [{ label: "No data", value: 0 }]} />
            </ChartCard>
          </div>

          <div className="admin-grid two">
            <ChartCard
              title="Product interest & affinity"
              subtitle="Views and clicks from selected session records"
            >
              <DataTable
                label="Product affinity"
                headings={["Product", "Views", "Clicks", "Interested customers", "Engagement"]}
              >
                {affinityRows.map((row) => (
                  <tr key={row.product}>
                    <td><strong>{row.product}</strong></td>
                    <td>{row.views}</td>
                    <td>{row.clicks}</td>
                    <td>{row.interested_customers}</td>
                    <td>{row.engagement_pct}%</td>
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
                  <strong>{data.session_analytics.total_sessions}</strong>
                </div>
                <div>
                  <span>Pages per session</span>
                  <strong>{data.session_analytics.pages_per_session.toFixed(1)}</strong>
                </div>
                <div>
                  <span>Returning customers</span>
                  <strong>{data.session_analytics.returning_customers}</strong>
                </div>
                <div>
                  <span>Average duration</span>
                  <strong>{duration(data.session_analytics.avg_duration_seconds)}</strong>
                </div>
              </div>
              <MiniTrend
                rows={months.map((m) => ({
                  label: new Intl.DateTimeFormat("en-IN", {
                    month: "short",
                    timeZone: "Asia/Kolkata",
                  }).format(new Date(`${m.month}-01T12:00:00+05:30`)),
                  value: m.count,
                }))}
              />
              <p className="admin-chart-caption">
                Recorded sessions by month; partial periods reflect the chosen dates.
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
                  <tr key={row.page}>
                    <td>{row.page}</td>
                    <td>{row.visits}</td>
                    <td>{row.unique_customers}</td>
                    <td>{duration(row.avg_time_seconds)}</td>
                  </tr>
                ))}
              </DataTable>
            </ChartCard>
            <ChartCard
              title="Common navigation journeys"
              subtitle="Simplified clickstream activity"
            >
              <div className="admin-flow-list">
                {journeyRows.length > 0 ? journeyRows.map((j, idx) => (
                  <div key={idx}>
                    <div>
                      {j.path.map((step, i) => (
                        <span key={step}>
                          {i > 0 && <span className="admin-flow-arrow">→</span>}
                          <b>{step}</b>
                        </span>
                      ))}
                    </div>
                    <small>{j.sessions} sessions</small>
                  </div>
                )) : (
                  <EmptyState message="Navigation journey data is not yet available." />
                )}
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
              {customers.map((c) => (
                <tr key={c.customer_id}>
                  <td>
                    <strong>{c.name}</strong>
                    <small>{c.customer_code}</small>
                  </td>
                  <td>{c.segment}</td>
                  <td>{c.product_interest ?? "—"}</td>
                  <td>{duration(c.avg_session_seconds)}</td>
                  <td>{c.engagement_pct}%</td>
                  <td>{c.top_spending_category ?? "—"}</td>
                  <td>
                    <RiskBadge risk={c.risk as "Low" | "Medium" | "High" | "Critical" | null} />
                  </td>
                  <td>
                    <Link
                      className="admin-table-link"
                      href={`/admin/customers/${c.customer_id}`}
                      aria-label={`View customer ${c.name}`}
                    >
                      View customer <ArrowUpRight size={14} />
                    </Link>
                  </td>
                </tr>
              ))}
            </DataTable>
            <p className="admin-chart-caption">
              Showing {customers.length} of {data.customer_behaviour.total} customers.
            </p>
          </ChartCard>
        </>
      )}
    </>
  );
}
