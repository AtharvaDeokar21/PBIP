import Link from "next/link";
import { ArrowUpRight, Landmark, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

export function Brand({ light = false }: { light?: boolean }) {
  return (
    <Link
      href="/"
      aria-label="Credora home"
      className={`brand ${light ? "brand-light" : ""}`}
    >
      <span className="brand-symbol">
        <Landmark size={23} />
      </span>
      <span>
        credora<span className="brand-dot">.</span>
      </span>
    </Link>
  );
}
export function SectionTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
        {description && <p className="muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
export function Money({ value }: { value: number }) {
  return (
    <>
      {new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
        maximumFractionDigits: 2,
      }).format(value)}
    </>
  );
}
export function SecurityNote() {
  return (
    <span className="security-note">
      <ShieldCheck size={15} /> Designed with your peace of mind in mind
    </span>
  );
}
export function TextLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link className="text-link" href={href}>
      {children}
      <ArrowUpRight size={16} />
    </Link>
  );
}
