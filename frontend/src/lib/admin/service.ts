import { adminSampleData } from "./sample-data";
import type { AdminSnapshot } from "./types";
// Replace this read-only adapter with agreed API calls; keep fixtures out of UI components.
export async function getAdminSnapshot(): Promise<AdminSnapshot> {
  return structuredClone(adminSampleData);
}
