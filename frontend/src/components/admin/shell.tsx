"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  ChartNoAxesCombined,
  ArrowUpRight,
  LogOut,
  Menu,
  X,
  Search,
  ChevronRight,
  Building2,
  FileText,
  ShieldAlert,
  ScanSearch,
  Scale,
} from "lucide-react";
import { Brand } from "@/components/ui";
import { clearToken } from "@/lib/admin/api";
const links = [
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/customers", label: "Customers", icon: Users },
  {
    href: "/admin/analytics",
    label: "Behaviour analytics",
    icon: ChartNoAxesCombined,
  },
];
const links2 = [
  { href: "/admin/audit-logs", label: "Audit Logs", icon: FileText },
  {
    href: "/admin/fraud",
    label: "Fraud & Security",
    icon: ShieldAlert,
  },
  {
    href: "/admin/investigations",
    label: "Fraud Investigation",
    icon: ScanSearch,
  },
  {
    href: "/admin/compliance",
    label: "Compliance & Risk",
    icon: Scale,
  },
];
export default function AdminShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const title = pathname.startsWith("/admin/customers/")
    ? "Customer details"
    : links.find((link) => pathname.startsWith(link.href))?.label ||
      links2.find((link) => pathname.startsWith(link.href))?.label ||
      "Dashboard";
  return (
    <div className="admin-app">
      <aside className={`admin-sidebar ${open ? "is-open" : ""}`}>
        <div className="admin-brand-row">
          <Brand />
          <button
            className="icon-button admin-mobile"
            aria-label="Close admin navigation"
            onClick={() => setOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <span className="admin-workspace-label">
          <Building2 size={13} /> INTERNAL WORKSPACE
        </span>
        <div className="admin-nav-label">WORKSPACE</div>
        <nav aria-label="Internal banking navigation">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname.startsWith(link.href) ? "is-active" : ""}
              aria-current={pathname.startsWith(link.href) ? "page" : undefined}
              onClick={() => setOpen(false)}
            >
              <link.icon size={19} />
              {link.label}
              {pathname.startsWith(link.href) && <ChevronRight size={15} />}
            </Link>
          ))}
          <div className="admin-nav-label admin-nav-section-label">
            SECURITY
          </div>
          {links2.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname.startsWith(link.href) ? "is-active" : ""}
              aria-current={pathname.startsWith(link.href) ? "page" : undefined}
              onClick={() => setOpen(false)}
            >
              <link.icon size={19} />
              {link.label}
              {pathname.startsWith(link.href) && <ChevronRight size={15} />}
            </Link>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <div className="admin-team-card">
            <span className="admin-person-avatar">AS</span>
            <div>
              <strong>Alex Shah</strong>
              <small>Banking administrator</small>
            </div>
          </div>
          <Link href="/admin/login" onClick={() => clearToken()}>
            <LogOut size={17} /> Exit workspace
          </Link>
        </div>
      </aside>
      {open && (
        <button
          className="admin-nav-overlay"
          aria-label="Dismiss admin navigation"
          onClick={() => setOpen(false)}
        />
      )}
      <div className="admin-body">
        <header className="admin-header">
          <div className="admin-breadcrumb">
            <button
              className="icon-button admin-mobile"
              aria-label="Open admin navigation"
              onClick={() => setOpen(true)}
            >
              <Menu size={22} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>{title}</strong>
          </div>
          <form
            className="admin-header-search"
            onSubmit={(event) => {
              event.preventDefault();
              router.push(
                `/admin/customers?q=${encodeURIComponent(search.trim())}`,
              );
            }}
          >
            <Search size={17} />
            <input
              aria-label="Find a customer"
              placeholder="Find a customer…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <button
              aria-label="Search customer directory"
              className="icon-button"
            >
              <ArrowUpRight size={16} />
            </button>
          </form>
          <div className="admin-employee">
            <span className="admin-person-avatar">AS</span>
            <div>
              <strong>Alex Shah</strong>
              <small>Administrator</small>
            </div>
          </div>
        </header>
        <main id="main" className="admin-main">
          {children}
        </main>
        <footer className="admin-footer">
          <span>© 2026 Credora · Internal banking workspace</span>
          <span>Illustrative records · API integration pending</span>
        </footer>
      </div>
    </div>
  );
}
