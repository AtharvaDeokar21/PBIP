import { Suspense } from "react";
import Analytics from "@/components/admin/analytics";
import { LoadingState } from "@/components/admin/ui";
export default function Page() {
  return (
    <Suspense fallback={<LoadingState />}>
      <Analytics />
    </Suspense>
  );
}
