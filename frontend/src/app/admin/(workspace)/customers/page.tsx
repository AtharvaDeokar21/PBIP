import { Suspense } from "react";
import Customers from "@/components/admin/customers";
import { LoadingState } from "@/components/admin/ui";
export default function Page() {
  return (
    <Suspense fallback={<LoadingState />}>
      <Customers />
    </Suspense>
  );
}
