import { notFound } from "next/navigation";
import CustomerPages from "@/components/customer-pages";
const sections = [
  "dashboard",
  "accounts",
  "payments",
  "payees",
  "statements",
  "scheduled",
  "loans",
  "wealth",
  "analytics",
  "recommendations",
  "notifications",
  "settings",
];
export function generateStaticParams() {
  return sections.map((section) => ({ section }));
}
export default async function Page({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;
  if (!sections.includes(section)) notFound();
  return <CustomerPages section={section} />;
}
