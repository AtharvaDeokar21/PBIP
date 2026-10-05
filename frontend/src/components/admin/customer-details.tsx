"use client";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  Wallet,
  Landmark,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Bell,
  Clock,
  MousePointer2,
  Layers,
} from "lucide-react";
import { Money } from "@/components/ui";
import { useAdminData } from "./use-admin-data";
import {
  totalBalance,
  activeAlerts,
  mean,
  duration,
  engagement,
  localDate,
} from "@/lib/admin/metrics";
import {
  PageTitle,
  StatCard,
  ChartCard,
  DataTable,
  RiskBadge,
  StatusBadge,
  LoadingState,
  ErrorState,
  EmptyState,
  HorizontalBars,
  MiniTrend,
} from "./ui";
export default function CustomerDetails({ id }: { id: string }) {
  const { data, loading, error, refresh } = useAdminData();
  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error} retry={refresh} />;
  const c = data.customers.find((customer) => customer.id === id);
  if (!c)
    return (
      <>
        <Link className="text-link" href="/admin/customers">
          <ArrowLeft size={16} /> Back to Customers
        </Link>
        <EmptyState
          title="Customer not found"
          message="This customer ID is not available in the current directory."
        />
      </>
    );
  const transactions = data.transactions
    .filter((t) => t.customerId === c.id)
    .sort((a, b) => b.date.localeCompare(a.date));
  const sessions = data.sessions.filter((s) => s.customerId === c.id);
  const alerts = data.alerts.filter((a) => a.customerId === c.id);
  const active = activeAlerts(data, c.id);
  const spending = [
    "Food",
    "Shopping",
    "Travel",
    "Utilities",
    "Entertainment",
    "Other",
  ].map((label) => ({
    label,
    value: transactions
      .filter((t) => t.type === "Debit" && t.category === label)
      .reduce((sum, t) => sum + t.amount, 0),
  }));
  const monthly = (type: "Credit" | "Debit") =>
    ["07", "08", "09", "10"].map((month, i) => ({
      label: ["Jul", "Aug", "Sep", "Oct"][i],
      value: transactions
        .filter((t) => t.type === type && t.date.startsWith(`2026-${month}`))
        .reduce((sum, t) => sum + t.amount, 0),
    }));
  return (
    <>
      <Link href="/admin/customers" className="text-link admin-back">
        <ArrowLeft size={16} /> Back to Customers
      </Link>
      <PageTitle
        title="Customer details"
        subtitle="One connected view of banking activity, behaviour and risk."
        action={
          <Link
            className="button secondary small"
            href={`/admin/analytics?customer=${c.id}`}
          >
            View full behaviour analytics <ArrowUpRight size={16} />
          </Link>
        }
      />
      <section className="admin-profile-card">
        <span className="admin-profile-avatar">
          {c.name
            .split(" ")
            .map((part) => part[0])
            .join("")}
        </span>
        <div>
          <h2>{c.name}</h2>
          <p>
            {c.id} <span>·</span> {c.email}
          </p>
          <div className="admin-profile-tags">
            <span className="admin-segment">{c.segment}</span>
            <RiskBadge risk={c.risk} />
            <span className="admin-badge">
              {active.length} active {active.length === 1 ? "alert" : "alerts"}
            </span>
          </div>
        </div>
        <div className="admin-profile-score">
          <small>Overall risk score</small>
          <strong>
            {c.riskScore}
            <span>/100</span>
          </strong>
        </div>
      </section>
      <div className="admin-stats six">
        <StatCard
          label="Total balance"
          value={<Money value={totalBalance(c)} />}
          icon={Wallet}
          note="Across associated accounts"
        />
        <StatCard
          label="Accounts"
          value={c.accounts.length}
          icon={Landmark}
          note="Accounts in the customer profile"
        />
        <StatCard
          label="Monthly income"
          value={<Money value={c.income} />}
          icon={TrendingUp}
          note="Illustrative monthly baseline"
        />
        <StatCard
          label="Monthly spending"
          value={<Money value={c.spending} />}
          icon={TrendingDown}
          note="Illustrative monthly baseline"
        />
        <StatCard
          label="Risk score"
          value={`${c.riskScore}/100`}
          icon={ShieldAlert}
          note={`${c.risk} overall risk`}
          tone={c.risk === "High" ? "red" : "purple"}
        />
        <StatCard
          label="Active alerts"
          value={active.length}
          icon={Bell}
          note="Unresolved customer signals"
          tone={active.length ? "amber" : "green"}
        />
      </div>
      <div className="admin-grid wide">
        <ChartCard title="Accounts" subtitle="Account numbers are masked">
          <DataTable
            label="Customer accounts"
            headings={["Account type", "Account number", "Balance", "Status"]}
          >
            {c.accounts.map((a) => (
              <tr key={a.id}>
                <td>{a.type}</td>
                <td>•••• •••• {a.lastFour}</td>
                <td className="admin-money">
                  <Money value={a.balance} />
                </td>
                <td>
                  <StatusBadge status={a.status} />
                </td>
              </tr>
            ))}
          </DataTable>
        </ChartCard>
        <ChartCard
          title="Existing products"
          subtitle="Products currently associated with this profile"
        >
          <div className="admin-product-list">
            {c.products.map((product) => (
              <div key={product}>
                <Landmark size={17} />
                <span>{product}</span>
                <StatusBadge status="Active" />
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
      <ChartCard
        title="Recent transactions"
        subtitle="Seven most recent recorded transactions · Credits and debits shown separately"
      >
        <DataTable
          label="Customer transactions"
          headings={[
            "Date",
            "Merchant / description",
            "Category",
            "Amount",
            "Type",
            "Status",
            "Risk",
          ]}
        >
          {transactions.slice(0, 7).map((t) => (
            <tr key={t.id}>
              <td className="admin-nowrap">{localDate(t.date)}</td>
              <td>
                <strong>{t.merchant}</strong>
                <small>{t.id}</small>
              </td>
              <td>{t.category}</td>
              <td
                className={`admin-money ${t.type === "Credit" ? "positive" : ""}`}
              >
                {t.type === "Credit" ? "+" : "−"}
                <Money value={t.amount} />
              </td>
              <td>{t.type}</td>
              <td>
                <StatusBadge status={t.status} />
              </td>
              <td>
                <RiskBadge risk={t.risk} />
              </td>
            </tr>
          ))}
        </DataTable>
      </ChartCard>
      <div className="admin-grid two">
        <ChartCard
          title="Spending insights"
          subtitle="Category distribution of recorded debit transactions"
        >
          <HorizontalBars rows={spending} money />
          <div className="admin-inline-metric">
            <span>Illustrative average monthly spending</span>
            <strong>
              <Money value={c.spending} />
            </strong>
          </div>
        </ChartCard>
        <ChartCard
          title="Income & spending pattern"
          subtitle="Monthly baselines and recorded customer activity"
        >
          <div className="admin-income-summary">
            <div>
              <span>Monthly income</span>
              <strong>
                <Money value={c.income} />
              </strong>
            </div>
            <div>
              <span>Monthly spending</span>
              <strong>
                <Money value={c.spending} />
              </strong>
            </div>
          </div>
          <div className="admin-comparison">
            <span
              style={{
                width: `${(c.income / (c.income + c.spending)) * 100}%`,
              }}
            />
            <span
              style={{
                width: `${(c.spending / (c.income + c.spending)) * 100}%`,
              }}
            />
          </div>
          <p className="admin-chart-caption">
            Regular salary income; shopping and other payments account for the
            largest recorded expenses. Monthly trends below use the recorded
            transaction amounts.
          </p>
          <h3 className="admin-small-heading">Monthly income trend</h3>
          <MiniTrend rows={monthly("Credit")} money />
          <h3 className="admin-small-heading">Monthly spending trend</h3>
          <MiniTrend rows={monthly("Debit")} money />
        </ChartCard>
      </div>
      <div className="admin-grid two">
        <ChartCard
          title="Risk & fraud information"
          subtitle="Customer-level signals; investigation actions are handled by the fraud team"
        >
          <div className="admin-risk-summary">
            <RiskBadge risk={c.risk} />
            <strong>
              {c.riskScore}
              <small>/100</small>
            </strong>
            <span>{active.length} active alerts</span>
          </div>
          {alerts.length ? (
            <div className="admin-signal-list">
              {alerts.map((a) => (
                <div key={a.id}>
                  <div>
                    <strong>{a.type}</strong>
                    <small>
                      {a.id} · {localDate(a.date, true)} IST
                    </small>
                  </div>
                  <RiskBadge risk={a.severity} />
                  <StatusBadge status={a.status} />
                </div>
              ))}
            </div>
          ) : (
            <p className="admin-subtle">
              No fraud or compliance incidents recorded for this profile.
            </p>
          )}
          <p className="admin-chart-caption">
            Previously resolved incidents:{" "}
            {alerts.filter((a) => a.status === "Resolved").length}. Risk scores
            are illustrative, not live assessments.
          </p>
        </ChartCard>
        <ChartCard
          title="Behaviour summary"
          subtitle="Platform interactions recorded for this customer"
        >
          <dl className="admin-summary-list">
            <div>
              <dt>
                <Layers size={15} /> Product interest
              </dt>
              <dd>{c.interest}</dd>
            </div>
            <div>
              <dt>
                <MousePointer2 size={15} /> Most visited sections
              </dt>
              <dd>{sessions[0]?.path.join(" → ") || "No recorded visits"}</dd>
            </div>
            <div>
              <dt>
                <Clock size={15} /> Average session
              </dt>
              <dd>{duration(mean(sessions.map((s) => s.seconds)))}</dd>
            </div>
            <div>
              <dt>Engagement</dt>
              <dd>{engagement(sessions)}% click-to-view ratio</dd>
            </div>
            <div>
              <dt>Recent activity</dt>
              <dd>
                {sessions.length
                  ? localDate(sessions[sessions.length - 1].date)
                  : "Not recorded"}
              </dd>
            </div>
            <div>
              <dt>Income pattern</dt>
              <dd>Regular monthly salary</dd>
            </div>
          </dl>
          <Link
            className="text-link"
            href={`/admin/analytics?customer=${c.id}`}
          >
            View full behaviour analytics <ArrowUpRight size={15} />
          </Link>
        </ChartCard>
      </div>
    </>
  );
}
