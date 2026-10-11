import { fetchAdminOverview } from "./api";
import type { AdminSnapshot } from "./types";

export async function getAdminSnapshot(): Promise<AdminSnapshot> {
  const overview = await fetchAdminOverview();
  return overview;
}
