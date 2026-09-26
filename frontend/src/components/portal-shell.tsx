"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Wallet,
  ArrowLeftRight,
  Users,
  ReceiptText,
  CalendarClock,
  Landmark,
  TrendingUp,
  ChartNoAxesCombined,
  Sparkles,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
  Send,
  MessageCircle,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { Brand } from "./ui";

const navigation = [
  { label: "Overview", slug: "dashboard", icon: LayoutDashboard },
  { label: "My accounts", slug: "accounts", icon: Wallet },
  { label: "Payments & transfers", slug: "payments", icon: ArrowLeftRight },
  { label: "My payees", slug: "payees", icon: Users },
  { label: "Statements", slug: "statements", icon: ReceiptText },
  { label: "Scheduled payments", slug: "scheduled", icon: CalendarClock },
  { label: "Loans", slug: "loans", icon: Landmark },
  { label: "Wealth & investments", slug: "wealth", icon: TrendingUp },
  { label: "Spending insights", slug: "analytics", icon: ChartNoAxesCombined },
  { label: "For you", slug: "recommendations", icon: Sparkles },
];
export default function PortalShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [menu, setMenu] = useState(false);
  const [chat, setChat] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; text: string }[]>(
    [],
  );
  const title =
    navigation.find((n) => pathname.startsWith(`/portal/${n.slug}`))?.label ||
    (pathname.includes("notifications")
      ? "Notifications"
      : "Profile & settings");
  function ask(text: string) {
    if (!text.trim()) return;
    const question = text.toLowerCase();
    const answer =
      question.includes("spend") || question.includes("expense")
        ? "In this sample, September spending is ₹34,200. Shopping is the largest category at ₹12,800. Open Spending insights to explore the breakdown."
        : question.includes("loan")
          ? "You can explore the loan catalogue and estimate monthly repayments with the EMI calculator. Eligibility and approval require a bank assessment; this sample cannot determine either."
          : question.includes("invest")
            ? "Explore the Wealth & investments page to compare illustrative product categories and their risks. This scripted sample does not provide personalized investment advice."
            : "I’m a scripted sample assistant. Try asking about spending, loans, or investments. Live AI responses and account access are planned for backend integration.";
    setMessages((m) => [
      ...m,
      { role: "user", text },
      { role: "assistant", text: answer },
    ]);
    setInput("");
  }
  return (
    <div className="portal">
      <aside className={`sidebar ${menu ? "open" : ""}`}>
        <div className="sidebar-brand">
          <Brand />
          <button
            className="icon-button mobile-only"
            aria-label="Close navigation"
            onClick={() => setMenu(false)}
          >
            <X />
          </button>
        </div>
        <span className="nav-caption">YOUR EVERYDAY</span>
        <nav aria-label="Customer navigation">
          {navigation.map((n) => (
            <Link
              key={n.slug}
              href={`/portal/${n.slug}`}
              onClick={() => setMenu(false)}
              className={
                pathname.startsWith(`/portal/${n.slug}`) ? "active" : ""
              }
              aria-current={
                pathname.startsWith(`/portal/${n.slug}`) ? "page" : undefined
              }
            >
              <n.icon size={18} />
              {n.label}
              {n.slug === "recommendations" && (
                <span className="new-badge">NEW</span>
              )}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <ShieldCheck size={23} />
            <strong>A little reminder</strong>
            <p>
              Never share your password or OTP. Even with someone who says
              they’re us.
            </p>
          </div>
          <Link href="/portal/settings">
            <Settings size={18} /> Profile & settings
          </Link>
          <Link
            href="/login"
            onClick={() => {
              sessionStorage.removeItem("credora-sample-name");
            }}
          >
            <LogOut size={18} /> Log out
          </Link>
        </div>
      </aside>
      {menu && (
        <button
          className="menu-overlay"
          aria-label="Close navigation overlay"
          onClick={() => setMenu(false)}
        />
      )}
      <div className="portal-body">
        <header className="portal-header">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-only"
              onClick={() => setMenu(true)}
              aria-label="Open navigation"
            >
              <Menu />
            </button>
            <span>Personal banking</span>
            <ChevronRight size={14} />
            <strong>{title}</strong>
          </div>
          <div className="header-actions">
            <span className="workspace-tag">PERSONAL BANKING</span>
            <Link
              className="icon-button notification-button"
              href="/portal/notifications"
              aria-label="View notifications"
            >
              <Bell size={20} />
              <i />
            </Link>
            <Link
              className="avatar"
              href="/portal/settings"
              aria-label="Open profile"
            >
              AD
            </Link>
          </div>
        </header>
        <div className="workspace-banner">
          <span className="tiny-dot" /> You’re exploring with sample data. No
          real accounts or payments are connected.
        </div>
        <main id="main" className="portal-main">
          {children}
        </main>
        <footer className="portal-footer">
          <span>
            © 2026 Credora · Personal banking, thoughtfully connected.
          </span>
          <span>
            <ShieldCheck size={13} /> Customer workspace
          </span>
        </footer>
      </div>
      <button
        className="assistant-toggle"
        onClick={() => setChat(!chat)}
        aria-expanded={chat}
        aria-controls="assistant-panel"
      >
        {chat ? <X size={19} /> : <Sparkles size={19} />}
        <span>{chat ? "Close assistant" : "Ask Credora"}</span>
      </button>
      {chat && (
        <section
          className="chat-panel"
          id="assistant-panel"
          aria-label="Sample banking assistant"
        >
          <header>
            <span className="icon-tile lavender">
              <Sparkles />
            </span>
            <div>
              <strong>Your banking companion</strong>
              <small>Scripted sample · No live AI connection</small>
            </div>
            <button
              className="icon-button"
              onClick={() => setMessages([])}
              aria-label="New conversation"
            >
              <MessageCircle size={18} />
            </button>
          </header>
          <div className="chat-messages" aria-live="polite">
            {messages.length === 0 ? (
              <div className="chat-welcome">
                <h3>
                  A little clarity,
                  <br />a conversation away.
                </h3>
                <p>What would you like to explore?</p>
                {[
                  "How much did I spend?",
                  "Explore my loan options",
                  "Tell me about investments",
                ].map((q) => (
                  <button key={q} onClick={() => ask(q)}>
                    {q}
                    <ArrowLeftRight size={14} />
                  </button>
                ))}
              </div>
            ) : (
              messages.map((m, i) => (
                <p key={i} className={`chat-message ${m.role}`}>
                  {m.text}
                </p>
              ))
            )}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
          >
            <input
              aria-label="Message to sample assistant"
              placeholder="Ask about your money…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={500}
            />
            <button
              className="icon-button"
              aria-label="Send message"
              disabled={!input.trim()}
            >
              <Send size={18} />
            </button>
          </form>
        </section>
      )}
    </div>
  );
}
