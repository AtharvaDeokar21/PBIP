"use client";
import Link from "next/link";
import {
  Users,
  ShieldAlert,
  ShieldCheck,
  ScanSearch,
  FileWarning,
  Activity,
  RefreshCw,
  ArrowUpRight,
  Clock,
} from "lucide-react";
import { useAdminData } from "./use-admin-data";
import {
  PageTitle,
  AdminHeaderDate,
  StatCard,
  ChartCard,
  DataTable,
  RiskBadge,
  StatusBadge,
  LoadingState,
  ErrorState,
  HorizontalBars,
  MiniTrend,
} from "./ui";
import { activeAlerts, engagement, localDate } from "@/lib/admin/metrics";
export default function Dashboard() {
  const { data, loading, error, refresh } = useAdminData();
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;
  const fraud = activeAlerts(data).filter((alert) => alert.domain === "Fraud");
  const investigation = fraud.filter((alert) => alert.status === "In review");
  const productRows = ["Savings", "Loans", "Investments", "Insurance"]
    .map((label) => ({
      label,
      value: data.sessions
        .filter((session) => session.product === label)
        .reduce((sum, session) => sum + session.views, 0),
    }))
    .sort((a, b) => b.value - a.value);
  return (
    <>
      <PageTitle
        title="Dashboard"
        subtitle="Overview of banking activity, customer behaviour and risk monitoring."
        action={
          <div className="admin-title-actions">
            <AdminHeaderDate snapshotDate={data.asOf} />
            <button className="button secondary small" onClick={refresh}>
              <RefreshCw size={15} /> Refresh
            </button>
          </div>
        }
      />
      <div className="admin-overview-banner">
        <div>
          <span className="admin-banner-icon">
            <ShieldCheck size={28} />
          </span>
          <div>
            <h2>A clearer view of your banking day.</h2>
            <p>
              {activeAlerts(data).length} active alerts across{" "}
              {data.customers.length} customer profiles. Start with the signals
              that matter.
            </p>
          </div>
        </div>
        <Link href="/admin/customers?alerts=active">
          Review customers <ArrowUpRight size={17} />
        </Link>
      </div>
      <div className="admin-stats six">
        <StatCard
          label="Total customers"
          value={data.customers.length}
          icon={Users}
          note="Across all customer segments"
          href="/admin/customers"
        />
        <StatCard
          label="Active fraud alerts"
          value={fraud.length}
          icon={ShieldAlert}
          tone="red"
          note={`${fraud.filter((a) => a.severity === "Critical").length} critical alert requiring attention`}
          href="/admin/customers?alerts=active"
        />
        <StatCard
          label="High-risk customers"
          value={data.customers.filter((c) => c.risk === "High").length}
          icon={ShieldAlert}
          tone="amber"
          note="Based on overall customer risk"
          href="/admin/customers?risk=High"
        />
        <StatCard
          label="Open investigations"
          value={investigation.length}
          icon={ScanSearch}
          note="Fraud alerts currently in review"
        />
        <StatCard
          label="Compliance alerts"
          value={
            data.summary?.complianceAlerts ??
            activeAlerts(data).filter((a) => a.domain === "Compliance").length
          }
          icon={FileWarning}
          tone="amber"
          note="Unresolved compliance signals"
        />
        <StatCard
          label="Customer engagement"
          value={`${engagement(data.sessions)}%`}
          icon={Activity}
          note="Average session click-to-view ratio"
          href="/admin/analytics"
        />
      </div>
      <div className="admin-grid wide">
        <ChartCard
          title="Recent alerts"
          subtitle="Latest fraud and compliance signals · All times IST"
          action={
            <Link className="text-link" href="/admin/customers?alerts=active">
              View customers <ArrowUpRight size={15} />
            </Link>
          }
        >
          <DataTable
            label="Recent alerts"
            headings={[
              "Alert",
              "Customer",
              "Type",
              "Severity",
              "Time",
              "Status",
            ]}
          >
            {data.alerts.map((alert) => (
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
                    {
                      data.customers.find((c) => c.id === alert.customerId)
                        ?.name
                    }
                  </Link>
                </td>
                <td>{alert.type}</td>
                <td>
                  <RiskBadge risk={alert.severity} />
                </td>
                <td className="admin-nowrap">{localDate(alert.date, true)}</td>
                <td>
                  <StatusBadge status={alert.status} />
                </td>
              </tr>
            ))}
          </DataTable>
        </ChartCard>
        <ChartCard
          title="Recent activity"
          subtitle="A timeline of important system events"
        >
          <div className="admin-activity">
            {data.activity.map((event) => (
              <Link
                key={event.id}
                href={`/admin/customers/${event.customerId}`}
              >
                <span className="admin-activity-dot" />
                <div>
                  <strong>{event.title}</strong>
                  <p>{event.detail}</p>
                  <small>
                    <Clock size={12} />
                    {localDate(event.date, true)} IST
                  </small>
                </div>
                <ArrowUpRight size={14} />
              </Link>
            ))}
          </div>
        </ChartCard>
      </div>
      <div className="admin-grid three">
        <ChartCard
          title="Product interest"
          subtitle="Product views across recorded sessions"
        >
          <HorizontalBars rows={productRows} />
        </ChartCard>
        <ChartCard
          title="Engagement trend"
          subtitle="Recorded sessions by month"
        >
          <MiniTrend
            rows={["07", "08", "09", "10"].map((month, i) => ({
              label: ["Jul", "Aug", "Sep", "Oct"][i],
              value: data.sessions.filter((s) =>
                s.date.startsWith(`2026-${month}`),
              ).length,
            }))}
          />
          <p className="admin-chart-caption">
            October includes records through 05 Oct.
          </p>
        </ChartCard>
        <ChartCard
          title="Customer segments"
          subtitle="Distribution across the customer base"
        >
          <HorizontalBars
            rows={["Standard", "Premium", "High Value"].map((label) => ({
              label,
              value: data.customers.filter((c) => c.segment === label).length,
            }))}
          />
          <Link className="text-link admin-chart-link" href="/admin/analytics">
            Explore behaviour analytics <ArrowUpRight size={15} />
          </Link>
        </ChartCard>
      </div>
    </>
  );
}
