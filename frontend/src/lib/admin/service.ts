import { adminSampleData } from "./sample-data";
import type { AdminSnapshot } from "./types";

// Replace this read-only adapter with agreed API calls; keep fixtures out of UI components.
// NOTE: The analytics page fetches live data directly via its own useBehaviourAnalytics hook.
export async function getAdminSnapshot(): Promise<AdminSnapshot> {
  return structuredClone(adminSampleData);
}
