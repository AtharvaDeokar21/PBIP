import type { Metadata } from "next";
import AuthPage from "@/components/auth-page";
export const metadata: Metadata = { title: "Admin login | Credora" };
export default function Page() {
  return <AuthPage mode="admin-login" />;
}
