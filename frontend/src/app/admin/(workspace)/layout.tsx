import type { Metadata } from "next";
import AdminShell from "@/components/admin/shell";
import "./admin.css";
export const metadata: Metadata = { title: "Internal banking | Credora" };
export default function Layout({ children }: { children: React.ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
