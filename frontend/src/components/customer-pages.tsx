"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  ArrowRight,
  ArrowDownLeft,
  Plus,
  Wallet,
  TrendingUp,
  Landmark,
  ReceiptText,
  ArrowLeftRight,
  Sparkles,
  ChevronRight,
  Search,
  ShieldCheck,
  Check,
  CalendarDays,
  CreditCard,
  Zap,
  Smartphone,
  Wifi,
  Flame,
  Bell,
  X,
  Trash2,
  Pencil,
  Download,
  CircleCheck,
  RefreshCcw,
  Loader2,
} from "lucide-react";
import { Money, SectionTitle, TextLink } from "./ui";
import {
  useCustomerSummary,
  useCustomerProfile,
  saveProfile,
  useAccounts,
  useTransactions,
  usePayees,
  submitTransfer,
  cancelATransfer,
  useBillers,
  submitBillPayment,
  useBillHistory,
  useLoanProducts,
  useLoanApplications,
  checkEligibility,
  submitLoanApplication,
  useInvestmentProducts,
  useTransfers,
  type Transfer,
  useHoldings,
  buyInvestment,
  useInsuranceProducts,
  useRecommendations,
  type Account,
  type Transaction,
  type Payee,
  type LoanProduct,
  type LoanEligibilityResponse,
  type InvestmentProduct,
} from "./use-customer-api";
import {
  accounts as sampleAccounts,
  transactions as sampleTransactions,
  initialPayees as sampleInitialPayees,
  products as sampleProducts,
  spending,
  type Transaction as SampleTransaction,
} from "@/lib/sample-data";

// ─── Generic API state helpers ────────────────────────────────────────────────
function ApiState({
  loading,
  error,
  onRetry,
  empty,
}: {
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
  empty?: boolean;
}) {
  if (loading) {
    return (
      <div className="empty-state">
        <Loader2 size={28} className="spin" />
        <p className="muted">Loading…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="empty-state">
        <p className="form-error" role="alert">
          {error}
        </p>
        {onRetry && (
          <button className="text-link" onClick={onRetry}>
            <RefreshCcw size={15} /> Retry
          </button>
        )}
      </div>
    );
  }
  if (empty) {
    return (
      <div className="empty-state">
        <Search />
        <h3>Nothing to show</h3>
        <p>No records found.</p>
      </div>
    );
  }
  return null;
}

function PageHeading({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        <p className="muted">{description}</p>
      </div>
      {children}
    </div>
  );
}

function toDisplayTx(t: Transaction | SampleTransaction) {
  const isCredit =
    "transaction_type" in t
      ? t.transaction_type === "CREDIT"
      : (t as SampleTransaction).amount > 0;
  const amt =
    "amount" in t
      ? typeof t.amount === "string"
        ? Math.abs(parseFloat(t.amount))
        : Math.abs((t as SampleTransaction).amount)
      : 0;
  const label =
    ("merchant_name" in t && t.merchant_name) ||
    ("name" in t && (t as any).name) ||
    ("description" in t && t.description) ||
    ("transaction_reference" in t && t.transaction_reference) ||
    "Transaction";
  const initials =
    ("initials" in t && (t as any).initials) || label.slice(0, 2).toUpperCase();
  const dateStr =
    "transaction_date" in t
      ? t.transaction_date
      : (t as SampleTransaction).date
        ? `${(t as SampleTransaction).date}T12:00:00`
        : new Date().toISOString();
  const ref =
    "transaction_reference" in t
      ? t.transaction_reference
      : (t as SampleTransaction).id;
  const category = ("category" in t ? t.category : null) ?? "—";
  const status =
    "transaction_status" in t ? t.transaction_status : "Completed";
  return { id: t.id, isCredit, amt, label, initials, dateStr, ref, category, status };
}

function TransactionTable({
  data = [],
  compact = false,
}: {
  data?: (Transaction | SampleTransaction)[];
  compact?: boolean;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Transaction</th>
            <th>Date</th>
            {!compact && <th>Category</th>}
            <th className="align-right">Amount</th>
            <th className="align-right">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((raw) => {
            const t = toDisplayTx(raw);
            return (
              <tr key={t.id}>
                <td>
                  <div className="transaction-name">
                    <span
                      className={`transaction-icon ${t.isCredit ? "green" : "lavender"}`}
                    >
                      {t.isCredit ? <ArrowDownLeft size={18} /> : t.initials}
                    </span>
                    <span>
                      <strong>{t.label}</strong>
                      <small>{compact ? t.category : t.ref}</small>
                    </span>
                  </div>
                </td>
                <td className="muted nowrap">
                  {new Date(t.dateStr).toLocaleDateString("en-IN", {
                    day: "2-digit",
                    month: "short",
                  })}
                </td>
                {!compact && <td className="muted">{t.category}</td>}
                <td className={`align-right amount ${t.isCredit ? "positive" : ""}`}>
                  {t.isCredit ? "+" : "−"}
                  <Money value={t.amt} />
                </td>
                <td className="align-right">
                  <span className="status">{t.status}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {!data.length && (
        <div className="empty-state">
          <Search />
          <h3>No transactions found</h3>
          <p>Try another search or widen your filters.</p>
        </div>
      )}
    </div>
  );
}

function SpendingChart() {
  return (
    <div className="spending-layout">
      <div
        className="donut"
        role="img"
        aria-label="September spending: Shopping 12800, Food 8200, Bills 7400, Travel and other 5800 rupees"
      >
        <div>
          <small>Total spent</small>
          <strong>₹34,200</strong>
          <span>September 2026</span>
        </div>
      </div>
      <div className="chart-legend">
        {spending.map((s) => (
          <div key={s.name}>
            <span>
              <i style={{ background: s.color }} />
              {s.name}
            </span>
            <strong>
              <Money value={s.amount} />
            </strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function Dashboard() {
  const profileQuery = useCustomerProfile();
  const summaryQuery = useCustomerSummary();
  const accountsQuery = useAccounts();
  const primaryAccId = accountsQuery.data?.items?.[0]?.id ?? null;
  const txQuery = useTransactions(primaryAccId);

  const userName = profileQuery.data
    ? `${profileQuery.data.first_name} ${profileQuery.data.last_name}`
    : "Akhil Doshi";

  const totalBal = summaryQuery.data?.total_available_balance
    ? parseFloat(summaryQuery.data.total_available_balance)
    : 246950;

  const investBal = summaryQuery.data?.total_invested
    ? parseFloat(summaryQuery.data.total_invested)
    : 125000;

  const recentTxs =
    txQuery.data?.items && txQuery.data.items.length > 0
      ? txQuery.data.items.slice(0, 5)
      : sampleTransactions.slice(0, 5);

  return (
    <>
      <PageHeading
        title={`Good morning, ${userName} ☀`}
        description="Here’s your money at a glance. Let’s make today a good one."
      >
        <span className="date-chip">
          <CalendarDays size={16} /> 26 September 2026
        </span>
      </PageHeading>
      <div className="overview-grid">
        <div className="total-balance">
          <div>
            <span>Total available balance</span>
            <Wallet size={19} />
          </div>
          <h2>
            ₹2,46,950<span>.00</span>
          </h2>
          <p>
            <TrendingUp size={14} /> +8.2%{" "}
            <span>from last month · illustrative</span>
          </p>
          <div className="balance-accounts">
            <span>
              Savings <strong>₹1,82,450</strong>
            </span>
            <span>
              Current <strong>₹64,500</strong>
            </span>
            <Link href="/portal/accounts" aria-label="View accounts">
              <ArrowUpRight size={23} />
            </Link>
          </div>
        </div>
        <div className="stat-card">
          <span className="icon-tile lavender">
            <TrendingUp size={22} />
          </span>
          <span className="muted">Your investments</span>
          <strong>₹1,25,000</strong>
          <small className="positive">+ ₹8,450 total illustrative gains</small>
          <TextLink href="/portal/wealth">Explore portfolio</TextLink>
        </div>
        <div className="stat-card">
          <span className="icon-tile peach">
            <Landmark size={22} />
          </span>
          <span className="muted">Outstanding loan</span>
          <strong>₹3,40,000</strong>
          <small className="muted">Next EMI: ₹8,750 on 05 Oct</small>
          <TextLink href="/portal/loans">View loan details</TextLink>
        </div>
      </div>
      <section className="quick-actions" aria-label="Quick actions">
        {[
          { icon: ArrowLeftRight, text: "Transfer money", path: "payments" },
          { icon: ReceiptText, text: "Pay a bill", path: "payments?tab=bills" },
          { icon: Download, text: "Statements", path: "statements" },
          { icon: TrendingUp, text: "Start investing", path: "wealth" },
          { icon: Landmark, text: "Explore loans", path: "loans" },
        ].map((a) => (
          <Link key={a.text} href={`/portal/${a.path}`}>
            <span className="icon-tile">
              <a.icon size={21} />
            </span>
            {a.text}
            <ChevronRight size={16} />
          </Link>
        ))}
      </section>
      <div className="dashboard-columns">
        <section className="panel">
          <SectionTitle
            title="Spending this month"
            action={<TextLink href="/portal/analytics">View insights</TextLink>}
          />
          <SpendingChart />
          <div className="panel-note">
            <Sparkles size={17} />
            <span>
              A little win: you spent <strong>12% less</strong> than last month
              in this sample.
            </span>
          </div>
        </section>
        <section className="panel health-panel">
          <SectionTitle title="Your financial wellbeing" />
          <div className="health-score">
            <strong>
              82<span>/100</span>
            </strong>
            <span className="status">Looking healthy</span>
          </div>
          <div className="progress-track">
            <span style={{ width: "82%" }} />
          </div>
          <p className="muted">
            You’re building a good foundation. Keep a little aside for life’s
            unexpected moments.
          </p>
          <div className="health-row">
            <ShieldCheck size={18} />
            <span>Consistent savings</span>
            <Check size={17} />
          </div>
          <div className="health-row">
            <CircleCheck size={18} />
            <span>On-time repayments</span>
            <Check size={17} />
          </div>
          <small className="muted">
            Illustrative score, not a credit assessment.
          </small>
        </section>
      </div>
      <section className="panel transactions-panel">
        <SectionTitle
          title="Your latest activity"
          description="The little things and the bigger moments."
          action={<TextLink href="/portal/accounts">All transactions</TextLink>}
        />
        <TransactionTable data={recentTxs} compact />
      </section>
      <div className="recommendation-banner">
        <span className="icon-tile">
          <Sparkles size={26} />
        </span>
        <div>
          <span className="eyebrow">A LITTLE SOMETHING FOR YOU</span>
          <h3>Give your idle savings a new purpose.</h3>
          <p>Explore fixed deposits for the goals on your horizon.</p>
        </div>
        <Link className="button secondary" href="/portal/recommendations">
          Explore recommendations <ArrowUpRight size={17} />
        </Link>
      </div>
    </>
  );
}

function Accounts() {
  const [selected, setSelected] = useState("all");
  const [search, setSearch] = useState("");
  const [type, setType] = useState("all");
  const [category, setCategory] = useState("all");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [minimum, setMinimum] = useState("");
  const [maximum, setMaximum] = useState("");
  const [sort, setSort] = useState("newest");

  const accountsQuery = useAccounts();
  const rawAccounts = accountsQuery.data?.items;
  const accounts = rawAccounts && rawAccounts.length > 0
    ? rawAccounts.map((a: Account) => ({
        id: a.id,
        name: `${a.account_type.charAt(0) + a.account_type.slice(1).toLowerCase()} Account`,
        type: `${a.account_type.charAt(0) + a.account_type.slice(1).toLowerCase()} account`,
        number: a.account_number.slice(-4),
        balance: parseFloat(a.balance),
        branch: "Mumbai, Fort",
        ifsc: "SAMP0000482",
      }))
    : sampleAccounts;

  const account = accounts.find((a) => a.id === selected);

  const selectedAccId = selected === "all" ? (rawAccounts?.[0]?.id ?? null) : selected;
  const txQuery = useTransactions(selectedAccId);
  const rawTxs = txQuery.data?.items;
  const transactions: (Transaction | SampleTransaction)[] =
    rawTxs && rawTxs.length > 0 ? rawTxs : sampleTransactions;

  const filtered = transactions
    .filter((raw) => {
      const isCredit = "transaction_type" in raw ? raw.transaction_type === "CREDIT" : (raw as SampleTransaction).amount > 0;
      const amt = "amount" in raw ? (typeof raw.amount === "string" ? Math.abs(parseFloat(raw.amount)) : Math.abs((raw as SampleTransaction).amount)) : 0;
      const name = ("merchant_name" in raw && raw.merchant_name) || ("name" in raw && (raw as any).name) || ("description" in raw && raw.description) || "Transaction";
      const cat = ("category" in raw ? raw.category : null) ?? "";
      const date = "transaction_date" in raw ? (raw as Transaction).transaction_date.slice(0, 10) : (raw as SampleTransaction).date;
      const accId = "account_id" in raw ? (raw as Transaction).account_id : (raw as SampleTransaction).account;

      return (
        (selected === "all" || accId === selected) &&
        name.toLowerCase().includes(search.toLowerCase()) &&
        (type === "all" || (type === "credit" ? isCredit : !isCredit)) &&
        (category === "all" || cat === category) &&
        (!from || date >= from) &&
        (!to || date <= to) &&
        (!minimum || amt >= Number(minimum)) &&
        (!maximum || amt <= Number(maximum))
      );
    })
    .sort((a, b) => {
      const amtA = "amount" in a ? (typeof a.amount === "string" ? Math.abs(parseFloat(a.amount)) : Math.abs((a as SampleTransaction).amount)) : 0;
      const amtB = "amount" in b ? (typeof b.amount === "string" ? Math.abs(parseFloat(b.amount)) : Math.abs((b as SampleTransaction).amount)) : 0;
      const dateA = "transaction_date" in a ? (a as Transaction).transaction_date : (a as SampleTransaction).date;
      const dateB = "transaction_date" in b ? (b as Transaction).transaction_date : (b as SampleTransaction).date;

      return sort === "amount"
        ? amtB - amtA
        : sort === "oldest"
          ? dateA.localeCompare(dateB)
          : dateB.localeCompare(dateA);
    });

  const categories = Array.from(new Set(transactions.map((t) => t.category).filter(Boolean)));

  return (
    <>
      <PageHeading
        title="A home for your everyday."
        description="Your accounts, balances and every little transaction."
      />
      <div className="account-grid">
        {accounts.map((a) => (
          <button
            key={a.id}
            className={`account-card ${selected === a.id ? "selected" : ""}`}
            onClick={() => setSelected(a.id)}
            aria-pressed={selected === a.id}
          >
            <div>
              <span className="icon-tile lavender">
                <Wallet />
              </span>
              <span className="status">Active</span>
            </div>
            <h3>{a.name}</h3>
            <p>
              {a.type} · •••• {a.number}
            </p>
            <strong>
              <Money value={a.balance} />
            </strong>
            <span className="text-link">
              View account <ArrowUpRight size={16} />
            </span>
          </button>
        ))}
      </div>
      {account && (
        <section className="panel account-detail">
          <SectionTitle
            title={account.name}
            action={
              <button className="text-link" onClick={() => setSelected("all")}>
                Show all accounts <X size={15} />
              </button>
            }
          />
          <div className="detail-grid">
            <div>
              <small>Account holder</small>
              <strong>Akhil Doshi</strong>
            </div>
            <div>
              <small>Account number</small>
              <strong>•••• •••• {account.number}</strong>
            </div>
            <div>
              <small>Branch</small>
              <strong>{account.branch}</strong>
            </div>
            <div>
              <small>Illustrative IFSC</small>
              <strong>{account.ifsc}</strong>
            </div>
          </div>
        </section>
      )}
      <section className="panel">
        <SectionTitle
          title="Transaction history"
          action={
            <TextLink href="/portal/statements">View statements</TextLink>
          }
        />
        <div className="filters">
          <label className="search-input">
            <Search size={17} />
            <input
              aria-label="Search transactions"
              placeholder="Search transactions"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          <select
            aria-label="Transaction type"
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            <option value="all">All transactions</option>
            <option value="credit">Credit</option>
            <option value="debit">Debit</option>
          </select>
          <select
            aria-label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="all">All categories</option>
            {categories.map((c) => (
              <option key={c as string}>{c as string}</option>
            ))}
          </select>
          <select
            aria-label="Sort transactions"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="amount">Highest amount</option>
          </select>
        </div>
        <div className="filters">
          <label>
            From
            <input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            />
          </label>
          <label>
            To
            <input
              type="date"
              value={to}
              min={from}
              onChange={(e) => setTo(e.target.value)}
            />
          </label>
          <label>
            Minimum ₹
            <input
              type="number"
              min="0"
              value={minimum}
              onChange={(e) => setMinimum(e.target.value)}
              placeholder="0"
            />
          </label>
          <label>
            Maximum ₹
            <input
              type="number"
              min="0"
              value={maximum}
              onChange={(e) => setMaximum(e.target.value)}
              placeholder="Any amount"
            />
          </label>
        </div>
        {from && to && from > to ? (
          <p className="form-error" role="alert">
            End date must be on or after the start date.
          </p>
        ) : (
          <TransactionTable data={filtered} />
        )}
      </section>
    </>
  );
}

function Payments() {
  const [tab, setTab] = useState("transfer");
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("tab") === "bills")
      setTab("bills");
  }, []);
  const [step, setStep] = useState(0);
  const [account, setAccount] = useState("savings");
  const [payee, setPayee] = useState("p1");
  const [amount, setAmount] = useState("");
  const [remark, setRemark] = useState("");
  const [date, setDate] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [biller, setBiller] = useState("Electricity");
  const [consumer, setConsumer] = useState("");

  const accountsQuery = useAccounts();
  const payeesQuery = usePayees();
  const billersQuery = useBillers();

  const rawPayAccs = accountsQuery.data?.items;
  const accounts = rawPayAccs && rawPayAccs.length > 0
    ? rawPayAccs.map((a: Account) => ({
        id: a.id,
        name: `${a.account_type} Account`,
        number: a.account_number.slice(-4),
        balance: parseFloat(a.balance),
      }))
    : sampleAccounts;

  const initialPayees = payeesQuery.data && payeesQuery.data.length > 0
    ? payeesQuery.data.map((p) => ({
        id: p.id,
        name: p.name,
        bank: p.bank_name,
        number: p.account_number.slice(-4),
      }))
    : sampleInitialPayees;

  const from = accounts.find((a) => a.id === account) || accounts[0];
  const to = initialPayees.find((p) => p.id === payee) || initialPayees[0];

  function review(e: React.FormEvent) {
    e.preventDefault();
    const n = Number(amount);
    if (!Number.isFinite(n) || n <= 0)
      return setError("Enter an amount greater than ₹0.");
    if (n > from.balance)
      return setError("This amount exceeds your sample account balance.");
    if (n > 100000)
      return setError(
        "The sample transfer limit is ₹1,00,000 per transaction.",
      );
    setError("");
    setStep(1);
  }

  return (
    <>
      <PageHeading
        title="Make your next money move."
        description="Everyday payments, with a little more ease."
      />
      <div className="tabs">
        <button
          className={tab === "transfer" ? "active" : ""}
          onClick={() => {
            setTab("transfer");
            setStep(0);
            setError("");
          }}
        >
          Transfer money
        </button>
        <button
          className={tab === "bills" ? "active" : ""}
          onClick={() => {
            setTab("bills");
            setStep(0);
            setError("");
          }}
        >
          Pay a bill
        </button>
      </div>
      <div className="form-columns">
        <section className="panel form-panel">
          {step === 0 ? (
            <form onSubmit={review}>
              <SectionTitle
                title={
                  tab === "transfer"
                    ? "A little closer, with every transfer."
                    : "Your bills, taken care of."
                }
              />
              <label>
                From account
                <select
                  value={account}
                  onChange={(e) => setAccount(e.target.value)}
                >
                  {accounts.map((a) => (
                    <option value={a.id} key={a.id}>
                      {a.name} •••• {a.number}
                    </option>
                  ))}
                </select>
              </label>
              <p className="field-help">
                Available balance: <Money value={from.balance} />
              </p>
              {tab === "transfer" ? (
                <label>
                  To payee
                  <select
                    value={payee}
                    onChange={(e) => setPayee(e.target.value)}
                  >
                    {initialPayees.map((p) => (
                      <option value={p.id} key={p.id}>
                        {p.name} · {p.bank} •••• {p.number}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <>
                  <div className="biller-types">
                    {[
                      { name: "Electricity", icon: Zap },
                      { name: "Mobile", icon: Smartphone },
                      { name: "Internet", icon: Wifi },
                      { name: "Gas", icon: Flame },
                      { name: "Credit card", icon: CreditCard },
                      { name: "Other", icon: ReceiptText },
                    ].map((b) => (
                      <button
                        type="button"
                        aria-pressed={biller === b.name}
                        className={biller === b.name ? "selected" : ""}
                        key={b.name}
                        onClick={() => setBiller(b.name)}
                      >
                        <b.icon size={19} />
                        {b.name}
                      </button>
                    ))}
                  </div>
                  <label>
                    Consumer / bill reference
                    <input
                      required
                      value={consumer}
                      onChange={(e) => setConsumer(e.target.value)}
                      placeholder="Enter a sample bill reference"
                      maxLength={30}
                    />
                  </label>
                </>
              )}
              <label>
                Amount (₹)
                <input
                  type="number"
                  required
                  min="0.01"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                />
              </label>
              <label>
                Remarks (optional)
                <input
                  value={remark}
                  onChange={(e) => setRemark(e.target.value)}
                  placeholder="What’s this for?"
                  maxLength={120}
                />
              </label>
              {tab === "transfer" && (
                <label>
                  Schedule date (optional)
                  <input
                    type="date"
                    min={new Date().toLocaleDateString("en-CA")}
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                  />
                </label>
              )}
              {error && (
                <p className="form-error" role="alert">
                  {error}
                </p>
              )}
              <button className="button" type="submit">
                Review {tab === "transfer" ? "transfer" : "payment"}
                <ArrowRight size={17} />
              </button>
            </form>
          ) : step === 1 ? (
            <div>
              <SectionTitle
                title="One last look."
                description="Make sure everything is just right."
              />
              <div className="review-amount">
                <Money value={Number(amount)} />
              </div>
              <dl className="review-list">
                <div>
                  <dt>From</dt>
                  <dd>
                    {from.name} •••• {from.number}
                  </dd>
                </div>
                <div>
                  <dt>To</dt>
                  <dd>
                    {tab === "transfer" ? to.name : `${biller} · ${consumer}`}
                  </dd>
                </div>
                <div>
                  <dt>When</dt>
                  <dd>{date && tab === "transfer" ? date : "Immediately"}</dd>
                </div>
                <div>
                  <dt>Remarks</dt>
                  <dd>{remark || "—"}</dd>
                </div>
                <div>
                  <dt>Fee</dt>
                  <dd>₹0 (sample)</dd>
                </div>
              </dl>
              <p className="notice">
                This is a simulation. No money will be moved.
              </p>
              <div className="button-row">
                <button className="button secondary" onClick={() => setStep(0)}>
                  Edit details
                </button>
                <button className="button" onClick={() => setStep(2)}>
                  Continue <ArrowRight size={16} />
                </button>
              </div>
            </div>
          ) : step === 2 ? (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (otp !== "123456")
                  return setError(
                    "Use 123456 to complete this sample verification.",
                  );
                setError("");
                try {
                  if (tab === "transfer") {
                    await submitTransfer({
                      source_account_id: from.id,
                      destination_account_id: to.id,
                      amount: Number(amount),
                      remarks: remark || "Transfer",
                      scheduled_at: date || undefined,
                    }).catch(() => null);
                  } else {
                    await submitBillPayment({
                      account_id: from.id,
                      biller_id: billersQuery.data?.[0]?.id ?? "biller_001",
                      amount: Number(amount),
                    }).catch(() => null);
                  }
                } catch {
                  /* demo simulation */
                }
                setStep(3);
              }}
            >
              <span className="icon-tile lavender">
                <ShieldCheck />
              </span>
              <h2>Confirm it’s you.</h2>
              <p className="muted">
                Sample verification code: <strong>123456</strong>. No SMS has
                been sent.
              </p>
              <label>
                6-digit sample code
                <input
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  autoComplete="off"
                />
              </label>
              {error && (
                <p className="form-error" role="alert">
                  {error}
                </p>
              )}
              <div className="button-row">
                <button
                  type="button"
                  className="button secondary"
                  onClick={() => setStep(1)}
                >
                  Back
                </button>
                <button className="button">Confirm simulation</button>
              </div>
            </form>
          ) : (
            <div className="success-state" role="status">
              <span className="success-icon">
                <Check size={32} />
              </span>
              <span className="eyebrow">VERIFICATION COMPLETE</span>
              <h2>
                {date && tab === "transfer"
                  ? "Schedule preview confirmed."
                  : "That’s a successful practice run."}
              </h2>
              <p>
                <Money value={Number(amount)} /> to{" "}
                {tab === "transfer" ? to.name : biller}
              </p>
              <p className="muted">
                No money moved, no schedule was saved, and your balances are
                unchanged. A live receipt will be available after backend
                integration.
              </p>
              <button
                className="button"
                onClick={() => {
                  setStep(0);
                  setAmount("");
                  setOtp("");
                  setDate("");
                }}
              >
                Make another sample payment
              </button>
            </div>
          )}
        </section>
        <aside className="panel side-note">
          <span className="icon-tile lavender">
            <ShieldCheck />
          </span>
          <h3>A moment of care.</h3>
          <p>
            Double-check the recipient before every payment. We’ll never ask you
            to share a password or verification code.
          </p>
          <hr />
          <h4>Your transfer checklist</h4>
          <ul className="check-list">
            <li>
              <Check /> Confirm your payee
            </li>
            <li>
              <Check /> Check the amount
            </li>
            <li>
              <Check /> Review before you send
            </li>
          </ul>
          <TextLink href="/portal/payees">Manage your payees</TextLink>
        </aside>
      </div>
    </>
  );
}

function Payees() {
  const payeesApi = usePayees();
  const livePayees = payeesApi.data;
  const initialPayees = livePayees && livePayees.length > 0
    ? livePayees.map((p) => ({
        id: p.id,
        name: p.name,
        bank: p.bank_name,
        number: p.account_number.slice(-4),
      }))
    : sampleInitialPayees;

  const [payees, setPayees] = useState(initialPayees);
  const [editing, setEditing] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [bank, setBank] = useState("");
  const [number, setNumber] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (livePayees && livePayees.length > 0) {
      setPayees(livePayees.map((p) => ({
        id: p.id,
        name: p.name,
        bank: p.bank_name,
        number: p.account_number.slice(-4),
      })));
    }
  }, [livePayees]);

  function open(id: string) {
    const p = payees.find((p) => p.id === id);
    setEditing(id);
    setName(p?.name || "");
    setBank(p?.bank || "");
    setNumber(p?.number || "");
  }

  return (
    <>
      <PageHeading
        title="Your people. A little closer."
        description="Manage the people you pay regularly."
      >
        <button className="button" onClick={() => open("new")}>
          <Plus size={17} /> Add payee
        </button>
      </PageHeading>
      <p className="notice">
        Payee changes are previews for this page only. They reset when you
        navigate away; transfer payees remain sample data. Bank verification is
        not connected.
      </p>
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      <div className="account-grid">
        {payees.map((p) => (
          <section key={p.id} className="panel payee-card">
            <span className="avatar">
              {p.name
                .split(" ")
                .map((s) => s[0])
                .join("")}
            </span>
            <h3>{p.name}</h3>
            <p className="muted">
              {p.bank} · •••• {p.number}
            </p>
            <div className="button-row">
              <button
                className="button secondary small"
                onClick={() => open(p.id)}
              >
                <Pencil size={15} /> Edit
              </button>
              <button
                className="icon-button danger"
                aria-label={`Delete ${p.name}`}
                onClick={() => setDeleting(p.id)}
              >
                <Trash2 size={17} />
              </button>
            </div>
            {deleting === p.id && (
              <div className="notice">
                <p>Remove {p.name} from this sample list?</p>
                <button
                  className="text-link danger"
                  onClick={() => {
                    setPayees((ps) => ps.filter((x) => x.id !== p.id));
                    payeesApi.removePayee(p.id).catch(() => null);
                    setDeleting(null);
                    setNotice("Payee removed from this page preview.");
                  }}
                >
                  Confirm removal
                </button>
                <button className="text-link" onClick={() => setDeleting(null)}>
                  Keep payee
                </button>
              </div>
            )}
          </section>
        ))}
      </div>
      {editing && (
        <section className="panel form-panel inline-form">
          <SectionTitle
            title={editing === "new" ? "Add someone new" : "Edit payee"}
            action={
              <button
                className="icon-button"
                onClick={() => setEditing(null)}
                aria-label="Cancel editing"
              >
                <X />
              </button>
            }
          />
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const p = {
                id: editing === "new" ? `p${Date.now()}` : editing,
                name: name.trim(),
                bank: bank.trim(),
                number,
              };
              if (!p.name || !p.bank) return;
              if (editing === "new") {
                payeesApi.addPayee({
                  name: p.name,
                  bank_name: p.bank,
                  account_number: p.number.padStart(12, "0"),
                  ifsc_code: "BARC0001",
                  nickname: p.name,
                }).catch(() => null);
              } else {
                payeesApi.editPayee(editing, {
                  nickname: p.name,
                }).catch(() => null);
              }
              setPayees((ps) =>
                editing === "new"
                  ? [...ps, p]
                  : ps.map((x) => (x.id === editing ? p : x)),
              );
              setEditing(null);
              setNotice(
                "Payee saved in this page preview. Verification is pending backend integration.",
              );
            }}
          >
            <label>
              Full name
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={80}
              />
            </label>
            <label>
              Bank name
              <input
                required
                value={bank}
                onChange={(e) => setBank(e.target.value)}
                maxLength={60}
              />
            </label>
            <label>
              Account last four digits
              <input
                required
                inputMode="numeric"
                pattern="[0-9]{4}"
                maxLength={4}
                value={number}
                onChange={(e) => setNumber(e.target.value)}
              />
            </label>
            <button className="button">Save preview</button>
          </form>
        </section>
      )}
    </>
  );
}

function Statements() {
  const [account, setAccount] = useState("savings");
  const [period, setPeriod] = useState("1");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [view, setView] = useState(false);

  const accountsQuery = useAccounts();
  const rawStmtAccs = accountsQuery.data?.items;
  const accounts = rawStmtAccs && rawStmtAccs.length > 0
    ? rawStmtAccs.map((a: Account) => ({
        id: a.id,
        name: `${a.account_type} Account`,
        number: a.account_number.slice(-4),
      }))
    : sampleAccounts;

  const txQuery = useTransactions(account);
  const transactions: (Transaction | SampleTransaction)[] =
    txQuery.data?.items && txQuery.data.items.length > 0
      ? txQuery.data.items
      : sampleTransactions;

  const valid = period !== "custom" || Boolean(from && to && from <= to);
  const cutoff =
    period === "1"
      ? "2026-09-01"
      : period === "3"
        ? "2026-07-01"
        : "2026-04-01";

  const data = transactions.filter((t) => {
    const acc = "account_id" in t ? t.account_id : (t as SampleTransaction).account;
    const date = "transaction_date" in t ? t.transaction_date.slice(0, 10) : (t as SampleTransaction).date;
    return (
      acc === account &&
      (period === "custom"
        ? date >= from && date <= to
        : date >= cutoff && date <= "2026-09-30")
    );
  });

  return (
    <>
      <PageHeading
        title="Your story, in statements."
        description="A clear view of where your money has been."
      />
      <section className="panel no-print">
        <SectionTitle
          title="Build your statement"
          description="Sample statements use September 2026 as the current month."
        />
        <div className="filters">
          <label>
            Account
            <select
              value={account}
              onChange={(e) => {
                setAccount(e.target.value);
                setView(false);
              }}
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} •••• {a.number}
                </option>
              ))}
            </select>
          </label>
          <label>
            Period
            <select
              value={period}
              onChange={(e) => {
                setPeriod(e.target.value);
                setView(false);
              }}
            >
              <option value="1">September 2026</option>
              <option value="3">Last 3 months</option>
              <option value="6">Last 6 months</option>
              <option value="custom">Custom date range</option>
            </select>
          </label>
          {period === "custom" && (
            <>
              <label>
                From
                <input
                  type="date"
                  value={from}
                  onChange={(e) => {
                    setFrom(e.target.value);
                    setView(false);
                  }}
                />
              </label>
              <label>
                To
                <input
                  type="date"
                  min={from}
                  value={to}
                  onChange={(e) => {
                    setTo(e.target.value);
                    setView(false);
                  }}
                />
              </label>
            </>
          )}
          <button
            className="button"
            disabled={!valid}
            onClick={() => setView(true)}
          >
            View statement <ArrowRight size={16} />
          </button>
        </div>
        {!valid && (
          <p className="field-help">Choose a valid start and end date.</p>
        )}
      </section>
      {view && (
        <section className="panel statement-print">
          <SectionTitle
            title="Credora · Sample account statement"
            description={`${accounts.find((a) => a.id === account)?.name} · ${period === "custom" ? `${from} to ${to}` : `${cutoff} to 2026-09-30`}`}
            action={
              <button
                className="button secondary small no-print"
                onClick={() => window.print()}
              >
                <Download size={16} /> Print / save as PDF
              </button>
            }
          />
          <p className="notice">
            Illustrative transactions only. Not an official bank statement.
          </p>
          <TransactionTable data={data} />
        </section>
      )}
    </>
  );
}

function Scheduled() {
  const transfersQuery = useTransfers(1, 20, "SCHEDULED");
  const liveTransfers = transfersQuery.data?.items;

  const [items, setItems] = useState([
    {
      id: "1",
      name: "Monthly rent",
      amount: 18000,
      date: "2026-10-01",
      recurrence: "Monthly",
    },
    {
      id: "2",
      name: "Internet bill",
      amount: 999,
      date: "2026-10-05",
      recurrence: "Monthly",
    },
  ]);
  const [confirm, setConfirm] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);

  useEffect(() => {
    if (liveTransfers && liveTransfers.length > 0) {
      setItems(liveTransfers.map((t) => ({
        id: t.id,
        name: t.reference_number || `Transfer to ${t.destination_account_id || "Account"}`,
        amount: parseFloat(t.amount),
        date: t.scheduled_at ? t.scheduled_at.slice(0, 10) : t.created_at.slice(0, 10),
        recurrence: "Monthly",
      })));
    }
  }, [liveTransfers]);

  return (
    <>
      <PageHeading
        title="A little ahead of the everyday."
        description="Keep an eye on the payments coming up."
      />
      <p className="notice">
        Illustrative schedules. Changes last only while this page is open.
      </p>
      <section className="panel">
        {items.length ? (
          items.map((item) => (
            <div className="scheduled-row" key={item.id}>
              <span className="icon-tile lavender">
                <CalendarDays />
              </span>
              <div>
                <h3>{item.name}</h3>
                <p className="muted">
                  {item.date} · {item.recurrence}
                </p>
              </div>
              <strong>
                <Money value={item.amount} />
              </strong>
              <button
                className="icon-button"
                aria-label={`Edit ${item.name}`}
                onClick={() => setEditing(editing === item.id ? null : item.id)}
              >
                <Pencil size={17} />
              </button>
              <button
                className="icon-button danger"
                aria-label={`Cancel ${item.name}`}
                onClick={() => setConfirm(item.id)}
              >
                <X size={18} />
              </button>
              {editing === item.id && (
                <label className="schedule-edit">
                  Next payment date
                  <input
                    type="date"
                    aria-label={`New date for ${item.name}`}
                    value={item.date}
                    min={new Date().toLocaleDateString("en-CA")}
                    onChange={(e) => {
                      if (e.target.value)
                        setItems((xs) =>
                          xs.map((x) =>
                            x.id === item.id
                              ? { ...x, date: e.target.value }
                              : x,
                          ),
                        );
                    }}
                  />
                  <button
                    className="text-link"
                    onClick={() => setEditing(null)}
                  >
                    Done
                  </button>
                </label>
              )}
              {confirm === item.id && (
                <div className="schedule-edit notice">
                  Cancel this sample schedule?
                  <button
                    className="text-link danger"
                    onClick={() => {
                      cancelATransfer(item.id).catch(() => null);
                      setItems((xs) => xs.filter((x) => x.id !== item.id));
                      setConfirm(null);
                    }}
                  >
                    Yes, cancel
                  </button>
                  <button
                    className="text-link"
                    onClick={() => setConfirm(null)}
                  >
                    Keep schedule
                  </button>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state">
            <CalendarDays />
            <h3>Nothing scheduled</h3>
            <p>You’ve removed all schedules from this preview.</p>
          </div>
        )}
      </section>
    </>
  );
}

function Loans() {
  const [amount, setAmount] = useState(500000);
  const [rate, setRate] = useState(10.5);
  const [months, setMonths] = useState(60);
  const [detail, setDetail] = useState<string | null>(null);

  const loanProductsQuery = useLoanProducts();
  const loanAppsQuery = useLoanApplications();

  const r = rate / 1200;
  const emi =
    r === 0
      ? amount / months
      : (amount * r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);

  return (
    <>
      <PageHeading
        title="Make room for your next chapter."
        description="Explore possibilities, and understand what they could look like."
      />
      <div className="loan-grid">
        {["Personal loan", "Home loan", "Education loan", "Vehicle loan"].map(
          (name, i) => (
            <section className="panel product-card" key={name}>
              <span className="icon-tile lavender">
                <Landmark />
              </span>
              <h3>{name}</h3>
              <p className="muted">
                {
                  [
                    "For the plans that matter to you.",
                    "A place to make your own.",
                    "A brighter start to tomorrow.",
                    "Take the next turn in your journey.",
                  ][i]
                }
              </p>
              <button className="text-link" onClick={() => setDetail(name)}>
                Explore details <ArrowUpRight size={16} />
              </button>
            </section>
          ),
        )}
      </div>
      {detail && (
        <section className="panel">
          <SectionTitle
            title={detail}
            action={
              <button
                className="icon-button"
                aria-label="Close loan details"
                onClick={() => setDetail(null)}
              >
                <X />
              </button>
            }
          />
          <p className="muted">
            Compare your budget using the calculator below. Rates shown are
            illustrative; actual rates, eligibility and approval depend on bank
            assessment. Applications and eligibility checks are planned for the
            next implementation phase.
          </p>
        </section>
      )}
      <div className="dashboard-columns">
        <section className="panel">
          <SectionTitle
            title="A little planning goes a long way."
            description="Estimate your monthly EMI. Illustrative rates only."
          />
          <div className="calculator">
            <label>
              Loan amount{" "}
              <strong>
                <Money value={amount} />
              </strong>
              <input
                aria-label="Loan amount"
                type="range"
                min="10000"
                max="5000000"
                step="10000"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
              />
            </label>
            <label>
              Annual interest rate <strong>{rate}%</strong>
              <input
                aria-label="Annual interest rate"
                type="range"
                min="0"
                max="24"
                step="0.1"
                value={rate}
                onChange={(e) => setRate(Number(e.target.value))}
              />
            </label>
            <label>
              Tenure <strong>{months} months</strong>
              <input
                aria-label="Tenure in months"
                type="range"
                min="6"
                max="360"
                step="6"
                value={months}
                onChange={(e) => setMonths(Number(e.target.value))}
              />
            </label>
          </div>
          <div className="emi-result" aria-live="polite">
            <span>Estimated monthly EMI</span>
            <strong>
              <Money value={Math.round(emi)} />
            </strong>
            <small>
              Total interest:{" "}
              <Money value={Math.round(emi * months - amount)} /> · Excludes
              fees
            </small>
          </div>
        </section>
        <section className="panel">
          <SectionTitle
            title="Your existing loan"
            description="Illustrative personal loan · •••• 2106"
          />
          <div className="review-amount">₹3,40,000</div>
          <p className="muted">Outstanding principal</p>
          <dl className="review-list">
            <div>
              <dt>Monthly EMI</dt>
              <dd>₹8,750</dd>
            </div>
            <div>
              <dt>Next due</dt>
              <dd>05 October 2026</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span className="status">On track</span>
              </dd>
            </div>
          </dl>
          <div className="panel-note">
            <Check size={17} /> A little consistency makes a big difference.
          </div>
        </section>
      </div>
    </>
  );
}

function Wealth() {
  const [compare, setCompare] = useState<string[]>([]);
  const [detail, setDetail] = useState<string | null>(null);

  const invQuery = useInvestmentProducts();
  const holdingsQuery = useHoldings();

  const products = sampleProducts;

  return (
    <>
      <PageHeading
        title="For the future you’re imagining."
        description="Explore ways to save, invest and protect what matters."
      />
      <p className="notice">
        Illustrative product categories, not offers or investment advice. No
        purchases or applications are available.
      </p>
      <div className="loan-grid">
        {products.map((p) => (
          <section className="panel product-card" key={p.name}>
            <span className="icon-tile lavender">
              <TrendingUp />
            </span>
            <span className="eyebrow">{p.category}</span>
            <h3>{p.name}</h3>
            <p className="muted">{p.description}</p>
            <small>Risk: {p.risk}</small>
            <button className="text-link" onClick={() => setDetail(p.name)}>
              View details <ArrowUpRight size={16} />
            </button>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={compare.includes(p.name)}
                disabled={!compare.includes(p.name) && compare.length >= 3}
                onChange={(e) =>
                  setCompare((xs) =>
                    e.target.checked
                      ? [...xs, p.name]
                      : xs.filter((x) => x !== p.name),
                  )
                }
              />
              Compare product
            </label>
          </section>
        ))}
      </div>
      {detail && (
        <section className="panel">
          <SectionTitle
            title={detail}
            action={
              <button
                className="icon-button"
                onClick={() => setDetail(null)}
                aria-label="Close product details"
              >
                <X />
              </button>
            }
          />
          <p className="muted">
            {products.find((p) => p.name === detail)?.description} Product
            documentation, fees, provider terms and suitability must be reviewed
            before investing. Live details and investment journeys are pending
            integration.
          </p>
        </section>
      )}
      {compare.length > 0 && (
        <section className="panel">
          <SectionTitle
            title="A clearer comparison"
            description="Select up to three categories. Sample figures; terms vary by provider."
          />
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  {compare.map((n) => (
                    <th key={n}>{n}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>Risk</th>
                  {compare.map((n) => (
                    <td key={n}>{products.find((p) => p.name === n)?.risk}</td>
                  ))}
                </tr>
                <tr>
                  <th>Illustrative minimum</th>
                  {compare.map((n) => (
                    <td key={n}>
                      <Money
                        value={products.find((p) => p.name === n)!.minimum}
                      />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>Returns</th>
                  {compare.map((n) => (
                    <td key={n}>Not quoted in sample</td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}

function Analytics() {
  const summaryQuery = useCustomerSummary();

  return (
    <>
      <PageHeading
        title="Get to know your money better."
        description="Small patterns. Useful insights. A clearer picture."
      />
      <div className="overview-grid analytics-stats">
        {[
          {
            label: "September income",
            value: 83000,
            note: "Illustrative aggregate",
          },
          {
            label: "September spending",
            value: 34200,
            note: "12% less than August",
          },
          {
            label: "Set aside this month",
            value: 48800,
            note: "58.8% of sample income",
          },
        ].map((s) => (
          <div className="panel" key={s.label}>
            <span className="muted">{s.label}</span>
            <h2>
              <Money value={s.value} />
            </h2>
            <small className="positive">{s.note}</small>
          </div>
        ))}
      </div>
      <div className="dashboard-columns">
        <section className="panel">
          <SectionTitle
            title="Where it went"
            description="September 2026 · Illustrative aggregates"
          />
          <SpendingChart />
        </section>
        <section className="panel">
          <SectionTitle
            title="Income meets spending"
            description="Six months of illustrative activity"
          />
          <div
            className="bar-chart"
            role="img"
            aria-label="Income and expenses over six months: April 65000 and 30000; May 70000 and 40000; June 60000 and 34000; July 78000 and 45000; August 80000 and 38864; September 83000 and 34200 rupees"
          >
            {[
              [65, 30],
              [70, 40],
              [60, 34],
              [78, 45],
              [80, 38.864],
              [83, 34.2],
            ].map((v, i) => (
              <div className="bar-group" key={i}>
                <div>
                  <span style={{ height: `${v[0] * 2}px` }} />
                  <span style={{ height: `${v[1] * 2}px` }} />
                </div>
                <small>{["Apr", "May", "Jun", "Jul", "Aug", "Sep"][i]}</small>
              </div>
            ))}
          </div>
          <div className="bar-legend">
            <span>
              <i />
              Income
            </span>
            <span>
              <i />
              Spending
            </span>
          </div>
        </section>
      </div>
      <section className="panel">
        <SectionTitle
          title="A little perspective"
          action={
            <span className="pill">
              <Sparkles size={14} /> Sample insights
            </span>
          }
        />
        <div className="insights-list">
          <div>
            <TrendingUp />
            <h3>Your savings habit is growing.</h3>
            <p>
              In this sample, income exceeded spending by ₹48,800 in September.
            </p>
          </div>
          <div>
            <Wallet />
            <h3>Shopping takes the largest share.</h3>
            <p>
              ₹12,800, or about 37% of this month’s spending, went to shopping.
            </p>
          </div>
          <div>
            <Sparkles />
            <h3>Make a little room for a buffer.</h3>
            <p>
              Explore savings products as you plan for upcoming goals and
              unexpected expenses.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}

function Recommendations() {
  const recsQuery = useRecommendations();

  return (
    <>
      <PageHeading
        title="A little more you."
        description="Ideas for your next step, all in one place."
      />
      <p className="notice">
        These are static examples, not recommendations generated from your
        personal information.
      </p>
      <div className="recommendations-grid">
        {[
          {
            title: "Give your savings a purpose.",
            tag: "SAVE FOR TOMORROW",
            text: "Explore fixed deposits for money you can set aside for a planned period.",
            href: "wealth",
            icon: Wallet,
          },
          {
            title: "Start small. Think long term.",
            tag: "BUILD A HABIT",
            text: "Understand mutual funds, market risks and the possibilities of regular investing.",
            href: "wealth",
            icon: TrendingUp,
          },
          {
            title: "Plan for that bigger milestone.",
            tag: "MAKE YOUR NEXT MOVE",
            text: "Estimate monthly repayments before considering a personal or home loan.",
            href: "loans",
            icon: Landmark,
          },
          {
            title: "Protect what matters most.",
            tag: "A LITTLE PEACE OF MIND",
            text: "Explore insurance categories and the questions to ask before choosing cover.",
            href: "wealth",
            icon: ShieldCheck,
          },
        ].map((r) => (
          <section className="panel product-card" key={r.title}>
            <span className="icon-tile lavender">
              <r.icon />
            </span>
            <span className="eyebrow">{r.tag}</span>
            <h2>{r.title}</h2>
            <p className="muted">{r.text}</p>
            <TextLink href={`/portal/${r.href}`}>Explore your options</TextLink>
          </section>
        ))}
      </div>
    </>
  );
}

function Notifications() {
  const [read, setRead] = useState(false);
  const [response, setResponse] = useState("");
  return (
    <>
      <PageHeading
        title="You’re in the know."
        description="The updates that matter to your everyday."
      >
        <button
          className="button secondary"
          onClick={() => setRead(true)}
          disabled={read}
        >
          {read ? "All marked as read" : "Mark all as read"}
          <Check size={16} />
        </button>
      </PageHeading>
      <section className="panel notifications-list">
        {[
          {
            icon: ShieldCheck,
            title: "Let’s check a transaction",
            text: "A sample ₹18,500 payment to an unfamiliar merchant was flagged for review.",
            time: "Today, 09:42",
            alert: true,
          },
          {
            icon: Bell,
            title: "A new sign-in",
            text: "Sample sign-in from Chrome on Windows in Mumbai.",
            time: "Today, 09:30",
            alert: false,
          },
          {
            icon: ArrowLeftRight,
            title: "Transfer completed",
            text: "Your illustrative ₹2,000 transfer to Akhil Doshi is complete.",
            time: "Yesterday, 16:15",
            alert: false,
          },
          {
            icon: Landmark,
            title: "Loan application update",
            text: "Your sample application is under review.",
            time: "Yesterday, 11:10",
            alert: false,
          },
        ].map((n) => (
          <article key={n.title} className={read ? "read" : "unread"}>
            <span className={`icon-tile ${n.alert ? "peach" : "lavender"}`}>
              <n.icon />
            </span>
            <div>
              <span className="muted small-text">{n.time} · Sample event</span>
              <h3>{n.title}</h3>
              <p className="muted">{n.text}</p>
              {n.alert &&
                (response ? (
                  <p role="status" className="notice">
                    {response} Sample only; no case was sent to a bank.
                  </p>
                ) : (
                  <div className="button-row">
                    <button
                      className="button secondary small"
                      onClick={() =>
                        setResponse("Marked as recognized in this preview.")
                      }
                    >
                      This was me
                    </button>
                    <button
                      className="button small"
                      onClick={() =>
                        setResponse("Marked for investigation in this preview.")
                      }
                    >
                      Report transaction
                    </button>
                  </div>
                ))}
            </div>
            {!read && <span className="tiny-dot" />}
          </article>
        ))}
      </section>
    </>
  );
}

function Settings() {
  const profileQuery = useCustomerProfile();
  const [saved, setSaved] = useState(false);
  const [name, setName] = useState("Akhil Doshi");
  const [email, setEmail] = useState("akhil@example.com");
  const [phone, setPhone] = useState("");
  const [preferences, setPreferences] = useState([true, true, false]);

  useEffect(() => {
    if (profileQuery.data) {
      setName(`${profileQuery.data.first_name} ${profileQuery.data.last_name}`);
      setEmail(profileQuery.data.email);
      if (profileQuery.data.phone) setPhone(profileQuery.data.phone);
    }
  }, [profileQuery.data]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    try {
      await saveProfile({ phone: phone || undefined }).catch(() => null);
    } catch {
      /* demo offline */
    }
    setSaved(true);
  }

  return (
    <>
      <PageHeading
        title="Banking, on your terms."
        description="Your profile and the little preferences that make it yours."
      />
      <div className="dashboard-columns">
        <section className="panel form-panel">
          <SectionTitle
            title="Your personal details"
            description="Changes are held only while this page is open."
          />
          <form onSubmit={handleSave}>
            <label>
              Full name
              <input
                required
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setSaved(false);
                }}
              />
            </label>
            <label>
              Email address
              <input
                required
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setSaved(false);
                }}
              />
            </label>
            <label>
              Phone number
              <input
                type="tel"
                placeholder="Add a sample contact number"
                maxLength={20}
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value);
                  setSaved(false);
                }}
              />
            </label>
            <button className="button">
              Save preview <Check size={16} />
            </button>
            {saved && (
              <p className="notice" role="status">
                Profile preview updated. No account information was changed.
              </p>
            )}
          </form>
        </section>
        <section className="panel">
          <SectionTitle
            title="Keep me in the loop"
            description="Preview your notification preferences."
          />
          {[
            "Transaction updates",
            "Security alerts",
            "Product recommendations",
          ].map((p, i) => (
            <label className="preference-row" key={p}>
              {p}
              <input
                type="checkbox"
                checked={preferences[i]}
                onChange={(e) =>
                  setPreferences((ps) =>
                    ps.map((v, j) => (j === i ? e.target.checked : v)),
                  )
                }
              />
            </label>
          ))}
          <p className="field-help">
            Live banking security alerts may be mandatory.
          </p>
          <hr />
          <SectionTitle title="Security & access" />
          <p className="muted">
            Password changes, MFA enrolment, account settings and active-device
            management require backend integration. This sample has no
            authenticated session.
          </p>
          <Link href="/login" className="text-link">
            Exit to sign in <ArrowRight size={16} />
          </Link>
        </section>
      </div>
    </>
  );
}

export default function CustomerPages({ section }: { section: string }) {
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);
  const pages: Record<string, React.ReactNode> = {
    dashboard: <Dashboard />,
    accounts: <Accounts />,
    payments: <Payments />,
    payees: <Payees />,
    statements: <Statements />,
    scheduled: <Scheduled />,
    loans: <Loans />,
    wealth: <Wealth />,
    analytics: <Analytics />,
    recommendations: <Recommendations />,
    notifications: <Notifications />,
    settings: <Settings />,
  };
  return (
    <div inert={!ready} aria-busy={!ready}>
      {pages[section]}
    </div>
  );
}
