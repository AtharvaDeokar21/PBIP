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
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { Brand } from "./ui";
import { clearCustomerToken } from "@/lib/customer/api";
import AIChat, { AIChatToggle } from "./ai-chat";

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
  const title =
    navigation.find((n) => pathname.startsWith(`/portal/${n.slug}`))?.label ||
    (pathname.includes("notifications")
      ? "Notifications"
      : "Profile & settings");
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
          <Link href="/portal/settings">
            <Settings size={18} /> Profile & settings
          </Link>
          <Link
            href="/login"
            onClick={() => {
              clearCustomerToken();
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
      {/* AI Banking Assistant */}
      <AIChatToggle isOpen={chat} onClick={() => setChat(!chat)} />
      <AIChat isOpen={chat} onClose={() => setChat(false)} />
    </div>
  );
}
